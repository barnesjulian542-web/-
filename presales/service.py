import hashlib
import json
from pathlib import Path
from langchain_core.tools import StructuredTool
from langgraph.types import Command
from .analyzer import Analyzer
from .catalog import Catalog
from .exports import export_csv
from .models import Review
from .storage import Store, TaskBusyError
from .workflow import config, open_graph


class Workbench:
    def __init__(self, data_dir, catalog_path):
        self.data_dir = Path(data_dir)
        self.store = Store(self.data_dir)
        self.catalog = Catalog.load(catalog_path)

    @staticmethod
    def check_role(role):
        if role not in ("sales", "reviewer"):
            raise PermissionError("无效角色")

    def get(self, task_id, role):
        self.check_role(role)
        task = self.store.get(task_id)
        if role == "sales" and task["role"] != "sales":
            raise PermissionError("该任务包含审核角色可访问的资料")
        if task["status"] == "reviewing":
            try:
                with self.store.task_lock(task_id):
                    with open_graph(self.data_dir, Analyzer(self.catalog), self.store) as graph:
                        state = graph.get_state(config(task_id))
                        if "human_review" in state.next:
                            self.store.update(task_id, status="awaiting_review")
                            self.store.event(task_id, "review_recovered", {"reason": "审核占用已释放，恢复人工审核"})
                        elif "finalize" in state.next:
                            graph.invoke(None, config(task_id))
                    task = self.store.get(task_id)
            except TaskBusyError:
                pass
        return task

    def list_tasks(self, role):
        self.check_role(role)
        return self.store.list_tasks(role)

    def submit(self, customer, text, deployment="cloud", role="sales", version="3.2", mode="demo"):
        self.check_role(role)
        customer, text = customer.strip(), text.strip()
        if not customer or len(customer) > 100:
            raise ValueError("客户名称须为 1–100 字")
        if not text or len(text) > 20000:
            raise ValueError("需求须为 1–20000 字")
        if deployment not in ("cloud", "private") or mode not in ("demo", "live"):
            raise ValueError("部署方式或模式无效")
        fingerprint = hashlib.sha256(json.dumps([customer, text, deployment, role, version, mode,
            self.catalog.fingerprint], ensure_ascii=False).encode()).hexdigest()
        task_id, created = self.store.add_task(fingerprint, customer, text, role, deployment, version, mode)
        if not created:
            return task_id
        self.store.event(task_id, "task_created", {"mode": mode, "synthetic": True})
        return self._execute(task_id)

    def _execute(self, task_id):
        task = self.store.get(task_id)
        analyzer = Analyzer(self.catalog)
        try:
            with open_graph(self.data_dir, analyzer, self.store) as graph:
                graph.invoke({"task_id": task_id, "text": task["text"], "deployment": task["deployment"],
                              "role": task["role"], "version": task["version"], "mode": task["mode"]}, config(task_id))
        except Exception as exc:
            self.store.update(task_id, status="error", error=str(exc))
            self.store.event(task_id, "verification_failed", {"error": str(exc)})
        return task_id

    def retry_failed(self, task_id, role):
        self.get(task_id, role)
        with self.store.task_lock(task_id):
            task = self.store.get(task_id)
            if task["status"] != "error":
                raise ValueError("仅失败任务可以明确重试")
            self.store.event(task_id, "retry_requested", {"previous_error": task["error"], "mode": task["mode"]})
            self.store.update(task_id, status="running", error="")
            return self._execute(task_id)

    def review(self, task_id, decisions, role):
        if role != "reviewer":
            raise PermissionError("仅审核角色可提交审核")
        self.get(task_id, role)
        with self.store.task_lock(task_id):
            return self._review_locked(task_id, decisions, role)

    def _review_locked(self, task_id, decisions, role):
        task = self.store.get(task_id)
        if task["status"] != "awaiting_review":
            raise ValueError("该任务已审核或正在处理，不可重复提交审核")
        validated = [Review.model_validate(d) for d in decisions]
        by_id = {d.item_id: d for d in validated}
        if len(by_id) != len(validated) or set(by_id) != {i["requirement"]["id"] for i in task["items"]}:
            raise ValueError("须一次提交全部条目的审核，不可遗漏或重复")
        for item in task["items"]:
            decision = by_id[item["requirement"]["id"]]
            if decision.action != "approve":
                continue
            if decision.answer != item["answer"]:
                raise ValueError("修改后的答复尚未核验，请选择退回补充；当前只可批准原核验答复")
        self.store.claim_review(task_id)
        try:
            with open_graph(self.data_dir, Analyzer(self.catalog), self.store) as graph:
                graph.invoke(Command(resume=[d.model_dump() for d in validated]), config(task_id))
        except Exception:
            if self.store.get(task_id)["status"] == "reviewing":
                self.store.update(task_id, status="awaiting_review")
            raise
        return self.store.get(task_id)

    def create_ticket(self, task_id, item_id, role):
        if role != "reviewer":
            raise PermissionError("仅审核角色可创建测试工单")
        task = self.get(task_id, role)
        item = next((i for i in task["items"] if i["requirement"]["id"] == item_id), None)
        if not item or task["status"] != "reviewed" or item["reviewer_action"] != "approve" or item["status"] == "supported":
            raise ValueError("仅已批准的待确认或不支持条目可以创建测试工单")

        def create_local_ticket(title: str) -> dict:
            """为已经审核的能力缺口创建本地模拟工单，重复调用返回相同工单。"""
            return self.store.ticket(task_id, item_id, title)

        tool = StructuredTool.from_function(create_local_ticket)
        return tool.invoke({"title": item["requirement"]["text"]})

    def list_tickets(self, role):
        self.check_role(role)
        return self.store.list_tickets(role)

    def events(self, task_id, role):
        self.get(task_id, role)
        return self.store.events(task_id)

    def export(self, task_id, approved_only, role):
        return export_csv(self.get(task_id, role), approved_only)
