import time
from contextlib import contextmanager
from typing import TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt


class TaskState(TypedDict, total=False):
    task_id: str
    text: str
    deployment: str
    role: str
    version: str
    mode: str
    items: list[dict]
    stats: dict
    decisions: list[dict]


def build_graph(checkpointer, analyzer, store):
    def verify(state):
        started = time.perf_counter()
        items = analyzer.analyze(state["text"], deployment=state["deployment"], role=state["role"],
                                 version=state["version"], mode=state["mode"])
        stats = {**analyzer.last_usage, "seconds": round(time.perf_counter() - started, 4),
                 "retrieval": "capability_alias_and_character_terms", "catalog_hash": analyzer.catalog.fingerprint,
                 "synthetic": True}
        result = [i.model_dump() for i in items]
        store.update(state["task_id"], status="awaiting_review", items=result, stats=stats)
        store.event(state["task_id"], "verification_finished", stats)
        return {"items": result, "stats": stats}

    def human_review(state):
        decisions = interrupt({"task_id": state["task_id"], "message": "请逐条审核答复草稿"})
        return {"decisions": decisions}

    def finalize(state):
        decisions = {d["item_id"]: d for d in state["decisions"]}
        items = []
        for item in state["items"]:
            reviewed = dict(item)
            decision = decisions[item["requirement"]["id"]]
            reviewed.update(reviewer_action=decision["action"], reviewed_answer=decision["answer"],
                            reviewer_note=decision["note"])
            items.append(reviewed)
        store.update(state["task_id"], status="reviewed", items=items)
        store.event(state["task_id"], "review_finished", {"decisions": state["decisions"]})
        return {"items": items}

    graph = StateGraph(TaskState)
    graph.add_node("verify", verify)
    graph.add_node("human_review", human_review)
    graph.add_node("finalize", finalize)
    graph.add_edge(START, "verify")
    graph.add_edge("verify", "human_review")
    graph.add_edge("human_review", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile(checkpointer=checkpointer)


@contextmanager
def open_graph(directory, analyzer, store):
    with SqliteSaver.from_conn_string(str(directory / "checkpoints.sqlite")) as checkpointer:
        yield build_graph(checkpointer, analyzer, store)


def config(task_id):
    return {"configurable": {"thread_id": task_id}}
