# 有据 · 售前需求核验与答复工作台

一个用于 AI 产品经理求职展示的企业售前场景原型。针对虚构产品“云桥协同”，把客户要求与已审核产品资料逐条核对，保留证据、未确认范围和人工审核记录，并将能力缺口交接为本地测试工单。

全部客户、人员、产品能力和资料均为模拟数据。默认离线可用，无需 API 密钥。

## 在当前电脑运行

在 PowerShell 中执行：

```powershell
Set-Location 'F:\project\qiye'
.\.venv\Scripts\python.exe start_app.py --port 8504
```

浏览器打开 http://127.0.0.1:8504 。停止前台服务用 Ctrl+C。已启动时直接打开网址；8504 被占用可改为 8505。

当前项目有自己的 `.venv`，已安装并核对依赖。无需再次创建环境。原反馈工作台目录、配置和数据库未用于本项目。

## 第一次体验

1. 在“需求核验”保持“售前人员”和“离线演示”，选择西岭科技示例，点击“开始核验”。
2. 查看 7 项结果。企业微信、Excel 已支持；离线客户端、LDAP 明确不支持；AI 总结、两秒指标、香港数据驻留待确认。
3. 在“查看依据”逐项切换，检查当前资料、旧版本、未审核笔记和香港资料冲突。
4. 侧边栏切换“审核负责人”，在“逐条审核答复”检查文字，按条目选择批准或退回，勾选确认后保存。修改答复后须退回补充，更新资料再重新核验；不能直接批准未经核验的新文字。
5. 导出“已批准答复”。批准待确认答复不会把能力结论变成已支持。
6. 选择待确认或不支持条目，创建测试工单。重复点击返回同一工单，在“测试工单”页查看。
7. 重启服务后仍可读取任务、审核、工单与处理记录。

支持每行一项的文字输入，或 UTF-8 CSV（必须含 `requirement` 列）。示例文件为 `fixtures/Q001.csv` 等；有上传时优先处理 CSV。

## 真实模型模式

复制配置模板并填写**本项目自己的**模型密钥：

```powershell
Copy-Item -LiteralPath '.env.example' -Destination '.env'
notepad .env
```

已有 `.env` 时直接编辑，避免覆盖。默认示例使用通义千问兼容接口；也可配置其他支持工具结构化输出的 OpenAI 兼容服务。更改 `.env` 后重启服务，并在侧边栏选择“真实模型”。实际端点、模型和结构化输出能力需要用你提供的配置验收。

真实模式通过 LangChain 抽取完整客户要求；能力结论和答复仍由已审核资料与规则生成。模型遗漏原文、输出不合格或调用失败时停止核验，保存失败状态；不会自动伪装成离线成功。每次核验尝试最多一次内容生成请求，SDK 自动重试设为 0，生成请求超时 40 秒；失败后可明确点击重试，旧失败事件保留。这些是本项目运行限制，不是产品性能承诺。

DeepSeek 官方接口可保留模型显示名称，例如：

```dotenv
LLM_MODEL=DeepSeek-V4.1-Flash
LLM_BASE_URL=https://api.deepseek.com
```

程序在真实核验前读取官方 `/models` 列表（查询超时 20 秒），将显示名称解析为**同一条模型记录**的 API 编号；不会修改 `.env` 或自动选择其他模型。当前实测列表中，上述显示名称对应 `deepseek-flash`。名称无法唯一匹配时停止调用。为兼容强制工具结构化抽取，DeepSeek 请求使用非思考模式；原文与参数完整性检查保留。任务处理记录保存 `configured_model` 和 `api_model`，可追溯两者对应关系。

2026-10-11 已使用该配置成功核验一条模拟企业微信登录需求。此结果验证接口连通与本次抽取，不代表完整问卷的模型准确率。原任务、失败事件及数据库均保留；详情见 `docs/VALIDATION.md`。

可选择在 `.env` 配置 LangSmith 追踪。开启后内容将发往对应服务；默认未开启。

## 技术分工

| 组件 | 代码 | 用途 |
| --- | --- | --- |
| LangChain | `presales/retrieval.py`、`analyzer.py`、`service.py` | BaseRetriever、RunnableLambda、模型结构化抽取、测试工单 StructuredTool |
| LangGraph | `presales/workflow.py` | verify → human_review interrupt → finalize；Command 恢复与 SQLite 检查点 |
| Pydantic | `presales/models.py` | 资料、需求、引用、结论和审核输入契约 |
| Streamlit | `app.py`、`app_pages/` | 四个中文页面，原生控件与主题 |
| SQLite | `presales/storage.py` | 任务、结果、审核事件、工单及唯一约束 |

默认检索是“已知能力别名匹配 + 中文字符词项排序”，不是语义向量检索。工具由审核后的固定业务流程调用，未实现模型自主选择工具或多 Agent。

## 数据与文件

- `fixtures/catalog.json`：18 份模拟资料的正文、能力标签、权限、版本、部署方式和审核状态；旁边的 `documents/` 为可阅读 Markdown。
- `fixtures/questionnaires.json`：3 份模拟客户问卷。
- `fixtures/evaluation_cases.json`：26 个固定合成开发案例与预期。
- `runtime/data/workbench.sqlite`：运行任务与工单；`checkpoints.sqlite`：LangGraph 状态。保留它们即可保留演示记录。
- `evaluation/`：每轮独立 JSON；`latest.json` 为最近一轮副本。评测不写运行库。
- `.env`、`.venv`、运行库和日志由 `.gitignore` 排除。

## 检查和评测

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\evaluate.py
```

测试覆盖角色、完整需求、证据、参数、审核、导出、恢复、去重和页面交互。真实模型边界使用测试替身，不是联网模型验收。离线评测是开发规则回归，不能解释为模型准确率或真实用户收益。

重新生成模拟资料：` .\.venv\Scripts\python.exe scripts\generate_data.py `。这会覆盖 fixtures 中的模拟资料，不清空运行库；旧任务保留生成时的引用和资料哈希。

## 换电脑部署

使用 Python 3.11 或更高版本（当前实测 Python 3.14.5），在项目目录创建新虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe start_app.py --port 8504
```

锁文件保留本次实测完整依赖；`requirements.txt` 是主要依赖。无需配置密钥即可体验离线演示。

## 展示资料与边界

- [产品说明](docs/PRD.md)
- [演示脚本](docs/DEMO_SCRIPT.md)
- [架构与当前限制](docs/ARCHITECTURE.md)
- [实测验证记录](docs/VALIDATION.md)
- [求职项目表述](docs/PORTFOLIO.md)

当前为本地原型：角色切换不是身份认证；能力标签由模拟资料人工整理；范围检查采用有限受控词汇，未知表述可能保守地判待确认。改写后的文字须退回补充，尚不能自动验证它的语义。真实模型、真实企业资料、用户审核耗时与生产部署尚未验收。
