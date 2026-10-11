import streamlit as st
from presales.ui_context import role, workbench

st.title("测试工单", icon=":material/assignment:")
st.caption("审核后的能力缺口与待确认事项。工单只保存在本地模拟库，便于展示售前到产品的交接。")
tickets = workbench().list_tickets(role())
st.metric("已记录工单", len(tickets), border=True)
if tickets:
    st.dataframe([{"工单": t["id"], "客户要求": t["title"], "状态": t["status"],
                   "来源任务": t["task_id"], "来源需求": t["item_id"], "创建时间（UTC）": t["created_at"]}
                  for t in tickets], hide_index=True, alt="本地模拟能力缺口工单")
else:
    st.info("尚无工单。在需求核验中审核条目后，可为待确认或不支持的要求创建工单。")
