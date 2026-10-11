import json
from collections import Counter
import streamlit as st
from presales.exports import import_csv
from presales.models import CAPABILITY_LABELS, FLAG_LABELS, STATUS_LABELS
from presales.ui_context import TASK_LABELS, mode, presets, role, workbench

st.title("售前需求核验", icon=":material/fact_check:")
st.caption("从客户要求到产品证据，再到可审核的答复。云桥协同 · 3.2 · 模拟产品")
wb, current_role = workbench(), role()
tasks = wb.list_tasks(current_role)

columns = st.columns(4)
for column, label, value in zip(columns,
        ["客户核验任务", "待人工审核", "审核已完成", "已记录能力缺口"],
        [len(tasks), sum(t["status"] == "awaiting_review" for t in tasks),
         sum(t["status"] == "reviewed" for t in tasks), len(wb.list_tickets(current_role))]):
    column.metric(label, value, border=True)

examples = presets()
example_names = [q["name"] for q in examples]


def load_example():
    q = examples[example_names.index(st.session_state["preset"])]
    st.session_state["customer"] = q["customer"]
    st.session_state["requirements"] = q["requirements"]
    st.session_state["deployment"] = "企业云版" if q["deployment"] == "cloud" else "私有部署版"


if "requirements" not in st.session_state:
    st.session_state["preset"] = example_names[0]
    load_example()

with st.expander("新建客户核验", expanded=not tasks, icon=":material/add_circle:"):
    st.selectbox("示例客户问卷", example_names, key="preset", on_change=load_example)
    with st.form("new_task"):
        left, right = st.columns([2, 1])
        left.text_input("客户名称", key="customer", max_chars=100)
        right.selectbox("目标部署方式", ["企业云版", "私有部署版"], key="deployment")
        st.text_area("客户需求清单", key="requirements", height=200,
                     help="每行一项，保留客户原文。多能力的单行会按已知能力拆分。")
        uploaded = st.file_uploader("或导入需求 CSV", type=["csv"],
                                   help="UTF-8 CSV，包含 requirement 列；上传后优先使用 CSV。")
        st.caption("离线演示按已知能力与资料规则核验；真实模型模式用于抽取需求，需本项目单独配置。")
        submit = st.form_submit_button("开始核验", type="primary", icon=":material/play_arrow:", key="submit_task")
    if submit:
        try:
            text = import_csv(uploaded.getvalue()) if uploaded is not None else st.session_state["requirements"]
            with st.spinner("正在核对客户要求与产品证据…"):
                task_id = wb.submit(st.session_state["customer"], text,
                    deployment="cloud" if st.session_state["deployment"] == "企业云版" else "private",
                    role=current_role, mode=mode())
            st.session_state["task_select"] = task_id
            st.session_state["notice"] = "核验任务已保存，可以查看证据并进行审核。"
            st.rerun()
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))

if not tasks:
    with st.container(border=True):
        st.subheader("从一份客户需求开始")
        st.markdown("选择示例问卷并点击 **开始核验**。系统会保留需求原文，展示能力结论与资料来源。")
        st.caption("建议先体验西岭科技问卷：包含已支持、明确不支持、路线图、参数缺失和资料冲突。")
    st.stop()

task_map = {t["id"]: t for t in tasks}
if st.session_state.get("task_select") not in task_map:
    st.session_state["task_select"] = tasks[0]["id"]
st.selectbox("查看核验任务", list(task_map), key="task_select",
             format_func=lambda key: f"{task_map[key]['customer']} · {TASK_LABELS[task_map[key]['status']]} · {key}")
task = wb.get(st.session_state["task_select"], current_role)
if st.session_state.get("notice"):
    st.success(st.session_state.pop("notice"))
st.badge(TASK_LABELS[task["status"]], color="green" if task["status"] == "reviewed" else "orange")
st.caption(f"任务 {task['id']} · {'企业云版' if task['deployment'] == 'cloud' else '私有部署版'} · "
           f"{'离线规则演示' if task['mode'] == 'demo' else '真实模型抽取'} · "
           f"核验用时 {task['stats'].get('seconds', 0):.3f} 秒")
if task["status"] == "error":
    st.error(task["error"])
    st.caption("失败记录已保存。修正配置后可明确重试；重复提交不会自动调用。真实模式重试可能产生模型费用。")
    if st.button("重试此任务", icon=":material/refresh:"):
        try:
            with st.spinner("正在重试核验…"):
                wb.retry_failed(task["id"], current_role)
            st.rerun()
        except (ValueError, RuntimeError, PermissionError) as exc:
            st.error(str(exc))
    st.stop()
if not task["items"]:
    st.info("任务正在处理。请稍后刷新页面。")
    st.stop()

items = task["items"]
counts = Counter(i["status"] for i in items)
st.subheader("核验结果")
st.caption(f"{len(items)} 项要求 · 已支持 {counts['supported']} · 明确不支持 {counts['unsupported']} · 待确认 {counts['pending']}")
rows = [{"编号": i["requirement"]["id"], "客户要求": i["requirement"]["text"],
         "核验对象": CAPABILITY_LABELS.get(i["requirement"]["capability"], "未识别范围"),
         "能力结论": STATUS_LABELS[i["status"]], "需关注": "；".join(FLAG_LABELS.get(f, f) for f in i["flags"]),
         "审核": {None: "未审核", "approve": "已批准", "return": "已退回"}[i["reviewer_action"]]} for i in items]
st.dataframe(rows, hide_index=True, alt="客户需求核验结果与审核状态", width="stretch")

details, next_step = st.columns([2, 1])
with details:
    st.subheader("查看依据")
    selected = st.selectbox("选择需求", range(len(items)), key=f"detail_{task['id']}",
        format_func=lambda index: f"{items[index]['requirement']['id']} · {CAPABILITY_LABELS.get(items[index]['requirement']['capability'], '未识别范围')} · {items[index]['requirement']['text']}")
    item = items[selected]
    color = {"supported": "green", "unsupported": "red", "pending": "orange"}[item["status"]]
    st.badge(STATUS_LABELS[item["status"]], color=color)
    st.markdown(item["reason"])
    for citation in item["citations"]:
        label = "当前已审核依据" if citation["authoritative"] else "参考资料，不能单独确立能力"
        with st.expander(f"{citation['title']} · {citation['version']}", expanded=True):
            st.caption(f"{citation['doc_id']} · {label}")
            st.text(citation["quote"])
    if not item["citations"]:
        st.info("当前可访问资料没有本项依据。请向产品负责人确认。")
with next_step:
    with st.container(border=True):
        st.subheader("客户答复")
        st.markdown(item["reviewed_answer"] or item["answer"])
        if item["reviewer_action"]:
            st.caption("已批准" if item["reviewer_action"] == "approve" else "已退回")
    with st.container(border=True):
        st.subheader("下一步")
        if task["status"] != "reviewed":
            st.markdown("由审核负责人逐条检查证据和答复，保存审核结果。")
        elif item["reviewer_action"] != "approve":
            st.markdown("此条已退回。补充资料或调整要求后，重新创建核验任务。")
        elif item["status"] != "supported":
            st.markdown("为待确认或暂不支持的要求创建测试工单，交给产品负责人评估。")
            if st.button("创建测试工单", key=f"ticket_{task['id']}_{item['requirement']['id']}",
                         disabled=current_role != "reviewer", icon=":material/add_task:"):
                ticket = wb.create_ticket(task["id"], item["requirement"]["id"], current_role)
                st.success(f"已记录 {ticket['id']}；重复点击会返回同一工单。")
        else:
            st.markdown("已批准的答复可以导出，供售前整理交付。")

with st.expander("逐条审核答复", expanded=current_role == "reviewer" and task["status"] == "awaiting_review",
                 icon=":material/rate_review:"):
    st.caption("可批准原核验答复。修改文字后请退回补充，更新资料并重新核验；待确认状态不会升级为已支持。")
    if task["status"] == "reviewed":
        st.success("审核已保存，原始草稿和审核记录均可追溯。")
    else:
        with st.form(f"review_{task['id']}"):
            decisions = []
            for item in items:
                key = f"{task['id']}_{item['requirement']['id']}"
                with st.expander(f"{item['requirement']['id']} · {STATUS_LABELS[item['status']]} · {item['requirement']['text']}"):
                    action = st.selectbox("审核决定", ["批准当前答复", "退回补充"], key=f"action_{key}",
                                          disabled=current_role != "reviewer")
                    answer = st.text_area("答复文字（修改后需退回补充）", item["answer"], height=125, key=f"answer_{key}",
                                          disabled=current_role != "reviewer")
                    note = st.text_input("审核备注", key=f"note_{key}", disabled=current_role != "reviewer")
                    decisions.append(dict(item_id=item["requirement"]["id"],
                        action="approve" if action == "批准当前答复" else "return", answer=answer, note=note))
            confirmed = st.checkbox("我已逐条检查证据、答复和待确认范围", key="review_confirm",
                                    disabled=current_role != "reviewer")
            save = st.form_submit_button("保存全部条目的审核", type="primary", key="review_submit",
                                        disabled=current_role != "reviewer", icon=":material/check_circle:")
        if save:
            if not confirmed:
                st.error("请先逐条核对并勾选审核确认。")
            else:
                try:
                    wb.review(task["id"], decisions, current_role)
                    st.session_state["notice"] = "审核已保存，已批准的答复可以导出。"
                    st.rerun()
                except (ValueError, RuntimeError, PermissionError) as exc:
                    st.error(str(exc))

with st.container(horizontal=True):
    st.download_button("导出核验草稿", wb.export(task["id"], False, current_role),
                       f"{task['id']}_draft.csv", mime="text/csv", icon=":material/download:")
    exportable = task["status"] == "reviewed" and any(i["reviewer_action"] == "approve" for i in items)
    st.download_button("导出已批准答复", wb.export(task["id"], True, current_role) if exportable else b"",
                       f"{task['id']}_approved.csv", mime="text/csv", disabled=not exportable,
                       icon=":material/task_alt:")
with st.expander("处理记录与原始结果", icon=":material/history:"):
    st.dataframe([{"时间（UTC）": e["created_at"], "动作": e["event"], "内容": e["detail"]}
                  for e in wb.events(task["id"], current_role)], hide_index=True, alt="任务处理记录")
    st.json({"mode": task["mode"], "stats": task["stats"], "original_items": items})
