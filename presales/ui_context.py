import json
import os
from pathlib import Path
import streamlit as st
from .service import Workbench

ROOT = Path(__file__).resolve().parents[1]


@st.cache_resource(max_entries=8, show_spinner=False)
def resource(directory, catalog_mtime):
    return Workbench(directory, ROOT / "fixtures/catalog.json")


def workbench():
    directory = Path(os.getenv("WORKBENCH_DATA_DIR", str(ROOT / "runtime/data"))).resolve()
    return resource(str(directory), (ROOT / "fixtures/catalog.json").stat().st_mtime_ns)


@st.cache_data(max_entries=2, show_spinner=False)
def questionnaires(mtime):
    return json.loads((ROOT / "fixtures/questionnaires.json").read_text(encoding="utf-8"))


def presets():
    return questionnaires((ROOT / "fixtures/questionnaires.json").stat().st_mtime_ns)


def role():
    return "reviewer" if st.session_state.get("identity") == "审核负责人 · 林悦" else "sales"


def mode():
    return "live" if st.session_state.get("mode_choice") == "真实模型" else "demo"


TASK_LABELS = {"running": "处理中", "awaiting_review": "待人工审核", "reviewing": "审核处理中",
               "reviewed": "审核已完成", "error": "核验失败"}
