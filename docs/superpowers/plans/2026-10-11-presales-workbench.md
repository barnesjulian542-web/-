# 售前工作台实施计划

> For agentic workers: 使用 superpowers:executing-plans 在本会话逐步实施。用户已要求完成创作，沿用已选业务范围。

**Goal:** 在 F:\project\qiye 交付可启动、可审核、可恢复和可评测的售前需求核验原型。

**Architecture:** LangChain 负责输入/模型与证据检索，独立证据规则限制结论；LangGraph 使用 SQLite 检查点暂停审核，应用数据库事务保存结果与测试工单。页面调用统一 service API。

**Tech stack:** Python 3.14、Streamlit 1.65、LangChain、LangGraph、Pydantic 2、SQLite。

**Spec:** ../specs/2026-10-11-presales-workbench-design.md

## Global constraints

- 仅本目录写入；全部业务资料明确标注模拟；不修改已有反馈项目。
- 默认模式为离线规则演示；真实模式需独立模型配置，不能自动退回并伪装成功。
- 无证据/未审核/过期/路线图/冲突不确立已支持；权限在检索之前执行。
- 审核和测试工单有幂等与重启恢复；批准答复与草稿分开标注。

## Review focus

- 混合多个诉求时保留原文，并覆盖每个可识别能力。
- 历史资料和当前资料冲突时不能简单选择相似度最高的历史记录。
- 切换角色不能读取历史任务中权限更高的证据。
- 改写答复不能绕过支持状态与未确认承诺限制。
- 重复提交、CSV 公式文本、模型失败与进程重启不能造成重复执行或假成功。

## Task 1：证据核验与数据

Files: presales/models.py, catalog.py, retrieval.py, analyzer.py, scripts/generate_data.py, fixtures/*, tests/test_evidence.py。

Interfaces: `Catalog.load(path)`、`analyze(text, deployment, role, version, mode) -> list[Assessment]`；Assessment 保存 Requirement、status、answer、citations、flags。

- [x] 写固定预期测试：SSO 已支持、AI 总结路线图待确认、未知 SLA 待确认、当前资料矛盾待确认、旧版本隔离、角色过滤、混合诉求。
- [x] 运行并确认失败。
- [x] 生成模拟产品资料，实施检索与规则核验；加入真实模型提取适配。
- [x] 运行测试并确认通过。

## Task 2：审核、恢复和执行

Files: presales/storage.py, workflow.py, service.py, exports.py, tests/test_workflow.py。

Interfaces: `Workbench(data_dir, catalog_path)`；`submit(...) -> task_id`；`get(task_id, role)`；`review(task_id, decisions, role)`；`create_ticket(task_id, item_id, role)`；`export(task_id, approved_only, role)`。

- [x] 写测试：审核前导出失败、未知不得升级、审核后重启读取、工单重复调用同一 ID、非法角色拒绝、旧审核不能重复覆盖、CSV 公式字符处理。
- [x] 运行并确认失败。
- [x] 实施 SQLite、LangGraph interrupt/Command 和事务幂等；导出共用同一审核记录。
- [x] 运行完整测试。

## Task 3：界面、评测与交付

Files: app.py, .streamlit/config.toml, scripts/evaluate.py, tests/test_app.py, README.md, docs/*, start_app.py。

- [x] 写 AppTest：初始页面、预设问卷提交、逐条审核后导出可用、证据库与工单导航。
- [x] 实施原生界面，生成独立评测结果和真实 measured 统计。
- [x] 完成 PRD、架构/局限、演示脚本和可复现运行步骤。
- [x] 运行整个测试集、pip check、评测、页面与服务器健康检查；最终独立审查并处理重要发现。
