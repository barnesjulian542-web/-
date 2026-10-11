# 实施记录

日期：2026-10-11，Asia/Shanghai。用户授权完整创作；执行位于独立的新目录 F:\project\qiye。

设计和计划已保存。实施采用本会话执行，最终独立审查。

环境：原 Python 3.14 可执行程序可用。新虚拟环境 ensurepip 起初因沙箱默认 TEMP 不可写失败；改用本项目 .tmp 后 ensurepip 成功，原环境不改动。

设计决定：默认采用可解释的中文词项检索与离线规则演示，真实模型模式独立配置。代价是离线演示不能证明自然语言泛化或语义检索效果；在页面、README 和评测中明确说明。

接口预检：analyze 的 Assessment 被 workflow 与 exports 共同消费；所有状态通过同一 Pydantic 契约，角色检查由 service 与检索层共同执行。

Task 1 complete：12项初始失败测试 → 实施 → 12项通过；后续增加4类范围/模型遗漏检查，观察失败后修正。模拟资料18份，客户问卷3份。

Task 2 complete：14项初始失败测试 → 实施 → 全部通过。新增默认待确认草稿审核测试，发现否定承诺文字被词项规则误拦截；保留原草稿合法审核并修正，15项通过。

Task 3：四页原生界面已实施。AppTest初始因测试路径错误修正；Windows沙箱限制本机socket导致阻塞，诊断栈定位asyncio socketpair后在本机权限运行。表单测试按真实提交批次设置checkbox，不额外触发未提交rerun；页面测试3项通过。

固定开发案例首次结果：evaluation/20261011T115047666730Z_demo.json，26/26，模型调用0，完整输出保留。已运行pip check，无损坏依赖。正在完成独立审查和实际浏览器显示检查。

Final review：独立上下文只读审查发现混合未覆盖范围、改写承诺、审核锁中断、失败无法重试、CSV缺失值共5项；全部观察失败后修复。CSV虽初评Minor，但会中断正常导入，按实际影响纳入修复。

Final fixed：test_unknown_secondary_scope_cannot_be_supported、test_live_extraction_cannot_skip_another_known_capability、test_substantive_edits_must_return_to_verification、test_interrupted_review_is_recoverable_after_restart、test_failed_live_task_has_explicit_retry_after_configuration_fix、test_missing_cell_reports_value_error均RED→GREEN。另验证活跃锁与完成步骤中断。最终完整46项通过，日志runtime/tests.log。

设计决定：批准文字限于原核验答复，实质编辑仅能退回补充。代价是当前不能直接批准润色后的文字，需要更新资料并重新核验。

Task 3 complete：原生四页、真实模型可配置接口、26案例评测、PRD/架构/演示/运行与求职文档交付。浏览器200、健康200/ok、脚本错误0；1个模拟任务停在人工审核，没有审批真实业务。新目录没有既有Git分支，交付本地文件，未发布或建立远端。

2026-10-11 真实接口修复：用户要求保持 DeepSeek-V4.1-Flash。只读 `/models` 返回该显示名称及对应编号 deepseek-flash；原请求返回 HTTP 400，明确拒绝将显示名称用作调用编号。仅修正编号后，第二次 HTTP 400 明确指出思考模式不支持指定 tool_choice。先观察4项接口适配测试失败，再实现官方模型列表的精确匹配和非思考模式工具抽取；不改配置文件、不回退到其他模型。新增异常脱敏检查，既有桩测试隔离本机模型配置。

补测：51项自动测试通过，日志 runtime/tests-20261011-deepseek-fix.log；冻结26个规则案例全部通过，新一轮 evaluation/20261011T132432537785Z_demo.json，旧轮保留。修复前用 SQLite backup 备份两份数据库到 runtime/backups/before-deepseek-fix-20261011T132510Z。原失败任务 c493acd25e67 重试成功，保留全部26条既有事件，追加重试与成功事件，停在人工审核。真实抽取调用1次、输入685 tokens、输出61 tokens；.env 内容哈希前后相同。证据见 runtime/deepseek-verification-20261011T132510Z.json。
