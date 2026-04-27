# AITS MVP 上线前核对清单（可执行版）

## 0. 目标与范围
- 目标：确保当前 MVP 在目标环境可稳定跑通闭环：项目创建 -> 用例生成/保存 -> 执行 -> 结果查询 -> Webhook 通知。
- 范围：环境变量、Redis/Celery、Webhook 可达性、前后端联调顺序。

---

## 1) 环境变量核对（后端）
在启动前确认这些变量已配置（本地 `.env` 或部署平台）：

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`（生产建议 `0`）
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD`
- `CELERY_BROKER_URL`（例：`redis://redis:6379/0`）
- `CELERY_RESULT_BACKEND`（例：`redis://redis:6379/0`）
- `OPENAI_API_KEY`（如需真实 LLM）
- `LLM_TYPE`（默认 `openai`）
- `LLM_MODEL`、`LLM_FALLBACK_MODEL`（可选）

快速检查命令（Windows PowerShell）：

```powershell
cd d:\ai_study\ai_test-platform\backend
python manage.py check
```

---

## 2) 基础服务健康检查（DB / Redis / Django / Celery）

### 2.1 启动服务

```powershell
cd d:\ai_study\ai_test-platform
docker compose up -d db redis django
```

### 2.2 Redis 连通性
- 期望：Redis 6379 可连通，Celery 不再报 `ConnectionRefusedError`。

### 2.3 Celery Worker

```powershell
cd d:\ai_study\ai_test-platform\backend
celery -A config worker -l info
```

期望日志包含：
- broker/result 指向 Redis
- worker 正常 ready，无重连风暴

---

## 3) 数据库迁移与后端回归

```powershell
cd d:\ai_study\ai_test-platform\backend
python manage.py migrate --noinput
python manage.py test
```

- 期望：测试全绿；无 `System check` 错误。

---

## 4) Webhook 回调可达性核对

### 4.1 配置项目通知地址
- 在项目 `notification_url` 填可访问的 Webhook URL（钉钉/企微机器人）。

### 4.2 连通性验证（建议）
- 用 Postman/curl 对 webhook 发最小 JSON，确认平台返回 2xx。
- 若 webhook 有 IP 白名单，确认部署出口 IP 已放行。

### 4.3 执行后通知验证
- 触发一个 `ExecutionTask`。
- 期望：任务完成后 webhook 收到消息，内容含：
  - `task_id` / `project_id` / `status`
  - `summary`
  - `result_link`

---

## 5) 前后端联调顺序（建议按此顺序）

1. 登录态准备
   - 确保前端请求能带上后端认证态（cookie 或 token）。
2. 项目模块
   - 进入 `/projects`，能看到项目卡片。
3. API 用例管理
   - 进入 `/projects/:id/api-cases`，创建并保存脚本。
4. UI 用例管理
   - 进入 `/projects/:id/ui-cases`，创建并保存脚本。
5. AI 生成接口（可选真实）
   - 调 `/api/ai/generate-api-script/`、`/api/ai/generate-ui-script/`。
6. 执行与报告
   - 进入 `/projects/:id/executions`，选择用例触发执行。
   - 轮询看到 `pending -> running -> finished`。
7. 结果校验
   - `GET /api/executions/tasks/{id}/results/` 返回明细。
   - 失败用例含 `screenshots` 路径。
8. 通知校验
   - webhook 收到任务完成消息。

---

## 6) 上线阻断项（任一失败都不建议上线）

- Celery 无法稳定连接 Redis
- `python manage.py test` 有失败
- 执行任务无法落库 `ExecutionResult`
- `/api/executions/tasks/{id}/results/` 返回异常或无明细
- 配置了 `notification_url` 但 webhook 无法收到消息
- 前端关键页面路由异常（`/projects`、`/projects/:id/api-cases`、`/projects/:id/ui-cases`、`/projects/:id/executions`）

---

## 7) 发布后 30 分钟观察项

- Celery worker 日志是否有持续重试/异常堆栈
- Redis 连接数与内存是否异常增长
- 执行任务平均耗时、失败率
- webhook 返回码（2xx 比例）
- 前端控制台是否有接口 401/403/500 激增

---

## 8) 可选：快速命令清单

```powershell
# 1) 启动基础服务
cd d:\ai_study\ai_test-platform
docker compose up -d db redis django

# 2) 后端检查
cd d:\ai_study\ai_test-platform\backend
python manage.py check
python manage.py migrate --noinput
python manage.py test

# 3) Celery
celery -A config worker -l info

# 4) 前端
cd d:\ai_study\ai_test-platform\frontend
npm install
npm run dev
```
