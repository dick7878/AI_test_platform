# AITS Frontend

AITS（AI 自动化测试平台）前端工程，基于 Vue 3 + Vite + Element Plus，提供项目管理、API/UI 用例管理和执行报告页面。

## 技术栈

- Vue 3
- Vite
- Vue Router
- Pinia
- Element Plus
- Axios
- Monaco Editor

## 本地开发

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

默认访问地址：`http://localhost:5173`

### 3. 构建生产包

```bash
npm run build
```

### 4. 本地预览构建结果

```bash
npm run preview
```

## 开发代理与接口

- 前端请求基地址在 `src/api/http.js` 中配置为 `/api`。
- Vite 代理在 `vite.config.js` 中将 `/api` 转发到 `http://127.0.0.1:8000`。
- 本地还提供了一个调试接口：`/api/test`（由 Vite 插件直接返回 mock 数据）。

## 页面路由

路由定义在 `src/router/index.js`：

- `/projects`：项目列表页
- `/projects/:id`：项目详情页
- `/projects/:id/api-cases`：API 用例管理页
- `/projects/:id/ui-cases`：UI 用例管理页
- `/projects/:id/executions`：执行报告页

## 目录结构

```text
frontend/
  src/
    api/            # Axios 封装与业务 API
    components/     # 公共组件（如 Monaco 编辑器）
    router/         # 前端路由
    views/          # 页面级组件
    App.vue
    main.js
```

## 与后端联调建议

1. 先启动后端服务（默认 `http://127.0.0.1:8000`）。
2. 再启动前端 `npm run dev`。
3. 打开 `/projects` 检查项目列表接口是否可用。
4. 依次验证 API 用例、UI 用例、执行报告三条业务链路。

## 说明

- 当前 README 聚焦 MVP 阶段前端开发与联调。
- 如果后端地址变化，请同步更新 `vite.config.js` 的代理目标。
