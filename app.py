from dotenv import load_dotenv
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)
st.set_page_config(page_title="有据 · 售前核验工作台", page_icon=":material/fact_check:", layout="wide")

with st.sidebar:
    st.title("有据", icon=":material/fact_check:")
    st.caption("让每一项客户答复都有依据")
    st.selectbox("演示身份", ["售前人员 · 陈晨", "审核负责人 · 林悦"], key="identity")
    st.selectbox("运行模式", ["离线演示", "真实模型"], key="mode_choice")
    st.caption("身份切换用于本地角色演示。全部企业、人员和产品资料均为模拟数据。")

page = st.navigation([
    st.Page("app_pages/workbench.py", title="需求核验", icon=":material/fact_check:", default=True),
    st.Page("app_pages/knowledge.py", title="产品证据库", icon=":material/library_books:"),
    st.Page("app_pages/tickets.py", title="测试工单", icon=":material/assignment:"),
    st.Page("app_pages/evaluation.py", title="评测与项目说明", icon=":material/analytics:"),
])
page.run()
