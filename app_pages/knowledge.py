import streamlit as st
from presales.ui_context import role, workbench

st.title("产品证据库", icon=":material/library_books:")
st.caption("云桥协同的模拟资料。资料是否经过审核、是否适用当前版本，比文本相似度更重要。")
wb = workbench()
search = st.text_input("搜索标题或内容", placeholder="例如：企业微信、香港、LDAP")
records = [r for r in wb.catalog.visible(role()) if search.casefold() in (r.title + r.content).casefold()]
cols = st.columns(3)
cols[0].metric("可见资料", len(records), border=True)
cols[1].metric("已审核当前资料", sum(r.approved and r.lifecycle == "current" for r in records), border=True)
cols[2].metric("历史与待审核资料", sum(not r.approved or r.lifecycle != "current" for r in records), border=True)
st.dataframe([{"编号": r.id, "标题": r.title, "版本": r.version,
               "状态": {"current": "当前", "archived": "已归档", "roadmap": "路线图"}[r.lifecycle],
               "审核": "已审核" if r.approved else "待审核", "范围": "销售可见" if r.access == "sales" else "内部审核",
               "负责人": r.owner, "更新日期": r.updated_at} for r in records], hide_index=True, alt="可访问的产品资料目录")
if records:
    source = st.selectbox("阅读完整资料", records, format_func=lambda r: f"{r.id} · {r.title}")
    with st.container(border=True):
        st.subheader(source.title)
        st.caption(f"{source.id} · {source.version} · {source.updated_at} · 全部内容为虚构")
        st.markdown(source.content)
else:
    st.info("没有匹配资料。")
