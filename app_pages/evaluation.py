import json
import streamlit as st
from presales.ui_context import ROOT

st.title("评测与项目说明", icon=":material/analytics:")
st.caption("用于 AI 产品经理求职展示的企业场景原型。以下结果均来自明确标注的合成资料。")
path = ROOT / "evaluation/latest.json"
if path.exists():
    report = json.loads(path.read_text(encoding="utf-8"))
    cols = st.columns(3)
    cols[0].metric("固定合成案例", report["total"], border=True)
    cols[1].metric("核验结果匹配预期", f"{report['passed']}/{report['total']}", border=True)
    cols[2].metric("模型调用", report["model_calls"], border=True)
    st.caption(f"模式：离线规则演示 · 运行时间 {report['generated_at']} · 不是模型准确率或真实用户效果")
    st.dataframe([{"案例": r["id"], "要求": r["text"], "预期": r["expected"],
                   "实际": r["actual"], "通过": r["passed"], "耗时（秒）": r["seconds"]}
                  for r in report["cases"]], hide_index=True, alt="固定合成案例的首次核验结果")
else:
    st.info("尚未生成评测结果。运行 scripts/evaluate.py 后可在此查看。")

with st.container(border=True):
    st.subheader("本项目解决的任务")
    st.markdown("客户提出需求 → 检索适用资料 → 核验支持情况 → 人工审核答复 → 导出与能力缺口交接。")
    st.markdown("**可展示的产品判断**：无依据时保留待确认；路线图不能当成交付；版本与部署影响能力；资料冲突需要人工核对。")

with st.expander("技术分工与验证边界", expanded=True):
    st.markdown("""
- **LangChain**：检索器、需求处理链、真实模型抽取接口、本地工单工具。
- **LangGraph**：核验、人工暂停、恢复、完成；SQLite 检查点跨重启保存。
- **Pydantic**：资料、需求、结果与审核参数验证。
- **Streamlit**：客户需求、证据、审核、工单与评测页面。

默认演示使用已知能力别名、字符检索和业务规则；未实现语义向量检索或模型自主选择工具。
真实模式调用模型抽取需求，结论与答复仍由已审核资料和规则约束。
角色切换是本地模拟，尚未接入企业登录；没有真实企业试点或用户效率提升数据。
当前只允许批准原核验文字；改写须退回补充，更新资料后重新核验。
""")
st.download_button("下载项目说明", (ROOT / "docs/PRD.md").read_bytes() if (ROOT / "docs/PRD.md").exists() else b"",
                   "有据_项目说明.md", mime="text/markdown", icon=":material/download:")
