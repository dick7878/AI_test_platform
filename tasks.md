以下基于《AITS 架构设计文档 V1.0》产出，每个任务均满足：**一次代码改动**、**可独立验证**、**单一问题**、**明确 DoD**。严格按依赖排序，适合交给 Cursor 逐条执行。

---

# AITS MVP 构建任务清单（Cursor 单步可执行）

> 总任务数：**26 个**  
> 预计总耗时：约 **12–15 小时**（含调试）  
> 目标：端到端跑通 “创建项目 → AI 生成用例 → 手动执行 → 查看结果 → 收到通知”

---

## 阶段 0：项目骨架搭建（Docker + Django + Celery）

| 编号 | 任务                             | 描述                                                         | 依赖 | 完成标准（DoD）                                          | 预计 |
| ---- | -------------------------------- | ------------------------------------------------------------ | ---- | -------------------------------------------------------- | ---- |
| T001 | 初始化 Django 项目与 Docker 骨架 | 创建 `backend/` 目录，编写 `Dockerfile`, `docker-compose.yml`(django, db, redis)，`requirements/base.txt` 包含 Django/DRF/Celery/psycopg2 | 无   | `docker-compose up` 后看到 Django 欢迎页                 | 15m  |
| T002 | 配置 Django 多环境 & Celery      | 拆分 `settings/base.py`, `dev.py`，添加 `celery.py`，配置 Redis 作为 broker | T001 | 执行 `celery -A config worker -l info` 成功启动          | 10m  |
| T003 | 初始化前端 Vue3 项目             | `npm create vite@latest frontend -- --template vue`，安装 Element Plus、Axios、Pinia、Monaco Editor，配置 Vite 代理到 Django | T001 | `npm run dev` 看到 Vue 页面，调 `/api/test` 返回模拟数据 | 15m  |

---

## 阶段 1：用户与项目空间

| 编号 | 任务                                              | 描述                                                         | 依赖 | DoD                                      | 预计 |
| ---- | ------------------------------------------------- | ------------------------------------------------------------ | ---- | ---------------------------------------- | ---- |
| T004 | 扩展 User 模型，创建 `users` app                  | 创建 `UserProfile` 模型（与 User 一对一，增加 `dingtalk_id`），注册到 admin | T002 | 进入 Django Admin 可编辑 UserProfile     | 10m  |
| T005 | 创建 `projects` 模型 `Project` 和 `ProjectMember` | 实现 `Project`（名称、描述、owner）和 `ProjectMember`（project+user 唯一），加入 `BaseModel` 混入 | T004 | 在 Django shell 中成功创建项目并添加成员 | 15m  |
| T006 | 暴露项目 REST API                                 | 使用 DRF `ModelViewSet` 实现 Project 的 CRUD，权限限制为项目成员可访问；自动将创建者设 owner | T005 | 通过 Postman 创建项目、拉取项目列表      | 20m  |

---

## 阶段 2：API 测试模块

| 编号 | 任务                                 | 描述                                                         | 依赖       | DoD                                            | 预计 |
| ---- | ------------------------------------ | ------------------------------------------------------------ | ---------- | ---------------------------------------------- | ---- |
| T007 | 创建 `apitest` 模型 `ApiEnvironment` | 字段：project FK, name, base_url, headers(JSON), variables(JSON) | T005       | 通过 shell 为项目创建两套环境                  | 10m  |
| T008 | 创建 `ApiTestCase` 模型              | 字段按架构文档，包含 status(草稿/就绪), method, path, script 等 | T005       | 成功创建一条 API 用例记录                      | 10m  |
| T009 | 实现 API 用例 REST API               | GET/POST/PUT/DELETE，按 project 过滤，使用 DRF Serializer    | T008, T007 | 创建并编辑用例，前端可拉取列表                 | 25m  |
| T010 | Swagger/OpenAPI 解析导入端点         | 新增 `POST /api/projects/{id}/import-swagger/`，接收 JSON/YAML，解析出接口列表存入 `ApiTestCase`（状态=草稿，script 为空） | T009       | 上传 Swagger JSON 后，用例列表自动出现对应接口 | 25m  |

---

## 阶段 3：AI 服务集成

| 编号 | 任务                               | 描述                                                         | 依赖 | DoD                                                          | 预计 |
| ---- | ---------------------------------- | ------------------------------------------------------------ | ---- | ------------------------------------------------------------ | ---- |
| T011 | 创建 `ai` app，封装 LangChain 调用 | 实现 `call_llm(prompt)` 函数，从环境变量读取 LLM API Key/类型，能成功返回一段 Python 代码字符串 | T001 | 调用 `./manage.py shell` 执行 `call_llm("返回 hello world Python")` 得到正确代码 | 20m  |
| T012 | 编写 API 用例生成 Prompt 模板      | 在 `ai/prompts/api_gen.txt` 中编写模板，参数：接口列表 JSON。要求输出 pytest 代码 | T011 | 手动传入一个接口，AI 返回可运行的脚本                        | 20m  |
| T013 | 实现生成 API 用例端点              | `POST /api/ai/generate-api-script/`，接收接口 JSON，调用 LangChain，返回脚本字符串 | T012 | 在 Swagger 导入后调用此接口，得到脚本并保存到用例            | 20m  |

---

## 阶段 4：Web UI 测试模块

| 编号 | 任务                                               | 描述                                                         | 依赖 | DoD                                                          | 预计 |
| ---- | -------------------------------------------------- | ------------------------------------------------------------ | ---- | ------------------------------------------------------------ | ---- |
| T014 | 创建 `uitest` 模型 `UIEnvironment` 和 `UITestCase` | 字段参照架构文档，UITestCase 含 `script`, `elements_snapshot` | T005 | 创建环境和一个 UI 用例                                       | 10m  |
| T015 | 实现 UI 用例 REST API                              | CRUD 视图，支持项目隔离                                      | T014 | 前端可增加/编辑 UI 用例                                      | 20m  |
| T016 | 编写 UI 脚本生成 Prompt 及端点                     | 模板 `ai/prompts/ui_gen.txt`，接收需求文本，生成 Playwright+Pytest 脚本；实现 `POST /api/ai/generate-ui-script/` | T013 | 输入“打开登录页，用admin/admin登录，验证跳转”，返回可执行脚本 | 20m  |

---

## 阶段 5：执行引擎与结果收集

| 编号 | 任务                                                        | 描述                                                         | 依赖       | DoD                                                  | 预计 |
| ---- | ----------------------------------------------------------- | ------------------------------------------------------------ | ---------- | ---------------------------------------------------- | ---- |
| T017 | 创建 `executions` 模型 `ExecutionTask` 和 `ExecutionResult` | 字段参照架构文档，使用 GenericForeignKey 关联用例            | T005       | 在 shell 中创建任务和结果记录                        | 15m  |
| T018 | 编写 Celery 任务 `run_test_task`                            | 接收 task_id，创建临时 pytest 项目结构，写入 `conftest.py`（提供 fixtures），注入用例脚本，执行 `pytest`，收集 stdout 及 allure 原始数据（可选） | T017, T001 | 手动调用任务能跑完一个简单脚本并记录结果             | 30m  |
| T019 | 实现执行任务触发 API                                        | `POST /api/executions/tasks/` 接受 `{project_id, case_ids: [type:id], env_id}`，创建 ExecutionTask 并发送 Celery 任务 | T018       | 前端调用后任务状态从 pending 变为 finished，结果入库 | 25m  |
| T020 | 执行结果 API                                                | `GET /api/executions/tasks/{id}/results/` 返回该任务所有用例结果、截图、日志 | T018       | 执行完成后能拉取到详细结果                           | 15m  |
| T021 | 截图与日志存储                                              | 在 `conftest.py` 的 fixture 中增加失败自动截图，将文件保存到 `MEDIA_ROOT/screenshots`，路径写入 ExecutionResult | T020       | UI 用例失败后能看到截图链接                          | 20m  |

---

## 阶段 6：前端核心页面

| 编号 | 任务                 | 描述                                                         | 依赖       | DoD                                   | 预计 |
| ---- | -------------------- | ------------------------------------------------------------ | ---------- | ------------------------------------- | ---- |
| T022 | 实现项目列表页及路由 | 主页显示项目卡片，点击进入项目详情；路由 `/projects`, `/projects/:id` | T006       | 登录后能看见自己参与的项目，进入内部  | 20m  |
| T023 | 实现 API 用例管理页  | 表格展示用例，支持新建、编辑（Monaco Editor 编辑脚本）、右键变更状态 | T009, T013 | 能创建用例、粘贴 AI 生成代码、保存    | 30m  |
| T024 | 实现 UI 用例管理页   | 类似 API 用例页，支持在线编辑 Playwright 脚本                | T015, T016 | 能生成并保存 UI 脚本                  | 25m  |
| T025 | 实现执行与报告页     | 选择多个 API/UI 用例，选择环境，点击执行；实时轮询任务状态；显示结果列表、截图预览 | T019, T020 | 手动触发执行，看到通过/失败明细和截图 | 30m  |

---

## 阶段 7：通知与收尾

| 编号 | 任务              | 描述                                                         | 依赖 | DoD                             | 预计 |
| ---- | ----------------- | ------------------------------------------------------------ | ---- | ------------------------------- | ---- |
| T026 | 集成钉钉/企微通知 | 在 `ExecutionTask` 完成后发送 Webhook，项目模型增加 `notification_url`，通知内容包含摘要和结果链接 | T025 | 配置机器人 URL 后执行完收到消息 | 20m  |

---

> **使用说明**：  
> - 从 T001 开始，按编号顺序执行，每个任务完成后运行对应验证。  
> - 每个任务可作为一个 Cursor 指令，直接提供该条目内容即可。  
> - 所有模型变更后立即执行 `makemigrations && migrate`，保证数据库同步。  
> - 若遇阻塞，优先确保该任务前置项已通过验证。