# 小易小程序前端迁移 Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不改变后端业务逻辑、接口语义、数据库结构与知识库数据格式的前提下，让 `frontend-uniapp` 完整接入现有后端，使小程序版“小易”在功能与记忆上与原本地端保持一致。

**Architecture:** 后端视为冻结基线，只做读取、验证与回归，不为适配小程序修改行为。前端通过 uni-app 页面、条件编译与小程序原生 API 适配微信环境；所有网络、鉴权、上传、分页、错误提示均围绕现有 `backend/routers` 接口实现。优先完成 `Lab` 作为管理页样板，再复用请求模式收敛 `Staff`、`Chat Logs` 与上传闭环。

**Tech Stack:** Vue 3 Composition API, uni-app, Pinia, Axios, 微信开发者工具, FastAPI, SQLite, ChromaDB

---

### Task 1: 冻结后端基线并修复当前编译阻塞

**Files:**
- Modify: `frontend-uniapp/src/pages/admin/admin.vue`
- Modify: `frontend-uniapp/src/pages/admin/chat-logs.vue`
- Test: `frontend-uniapp/scripts/test-chat-logs-mp-mvp.cjs`
- Test: `frontend-uniapp/scripts/test-mp-weixin-build.cjs`（如有）

**Step 1: 修复 `admin.vue` 的条件编译与语法脏数据**

- 移除损坏的 `#ifdef / #endif` 片段或补齐配对。
- 保留 H5 独有上传逻辑在 `#ifdef H5` 内，小程序端只保留导航入口与基础卡片。
- 修复缺失的 `ref` import、损坏字符串、损坏模板文本。

**Step 2: 修复 `chat-logs.vue` 的条件编译骨架**

- 增加 `<!-- #ifndef H5 -->` 小程序模板标记与必要的 H5 包裹。
- 修复缺失 import：`resolveApiUrl`、`ensureAdminPageAccess`、H5 下的 `axios` 与 `renderMarkdown`。
- 修复损坏模板文本、字符串插值与导航逻辑。

**Step 3: 跑编译与现有脚本**

Run: `npm run test:chat-logs-mp-mvp`
Expected: PASS

Run: `npm run build:mp-weixin`
Expected: PASS，且不再报条件编译失败

### Task 2: 收敛 Lab 页面为管理页样板

**Files:**
- Modify: `frontend-uniapp/src/pages/admin/lab.vue`
- Reference: `frontend/src/views/LabView.vue`
- Reference: `backend/routers/settings.py`
- Test: `frontend-uniapp/scripts/test-lab-mp-state.cjs`
- Test: `frontend-uniapp/scripts/test-lab-mp-mvp.cjs`

**Step 1: 保持接口完全对齐**

- 仅调用 `GET /api/settings/` 与 `PATCH /api/settings/`
- 不修改 payload key，不变更 bool/string 映射规则

**Step 2: 强化小程序交互**

- 保留 slider / switch / textarea 方案
- 增加保存前 dirty 检测、同步状态、最后同步时间
- 所有错误统一走 toast + banner 状态

**Step 3: 处理权限与回退**

- 首屏执行 `ensureAdminPageAccess('lab')`
- 未授权直接回退，不新增后端权限逻辑

**Step 4: 回归验证**

Run: `npm run test:lab-mp-state`
Expected: PASS

Run: `npm run build:mp-weixin`
Expected: PASS

### Task 3: 完成 Staff 页面 CRUD 与组织结构闭环

**Files:**
- Modify: `frontend-uniapp/src/pages/admin/staff.vue`
- Reference: `frontend/src/views/StaffView.vue`
- Reference: `backend/routers/staff.py`
- Test: `frontend-uniapp/scripts/test-staff-mp-crud.cjs`
- Test: `frontend-uniapp/scripts/test-staff-mp-mvp.cjs`

**Step 1: 对齐现有接口**

- `GET /api/staff/users`
- `POST /api/staff/users`
- `PATCH /api/staff/users/{id}`
- `DELETE /api/staff/users/{id}`
- `GET /api/staff/structure`
- `POST /api/staff/branches`
- `POST /api/staff/departments`
- H5 保留 `GET /api/staff/users/export`

**Step 2: 收敛表单行为**

- 新建/编辑共用表单状态
- branch 改变时同步 department 默认值
- branch admin 权限只在前端做提示与禁用，不改变后端规则

**Step 3: 收敛反馈**

- 成功后刷新数据并关闭弹层
- 失败显示具体 `detail`
- 删除当前账号时直接前端阻断

**Step 4: 回归验证**

Run: `npm run test:staff-mp-crud`
Expected: PASS

Run: `npm run test:staff-mp-mvp`
Expected: PASS

### Task 4: 完成 Chat Logs 页面查询闭环

**Files:**
- Modify: `frontend-uniapp/src/pages/admin/chat-logs.vue`
- Reference: `frontend/src/views/ChatLogsView.vue`
- Reference: `backend/routers/chat_logs.py`
- Test: `frontend-uniapp/scripts/test-chat-logs-mp-mvp.cjs`
- Test: `frontend-uniapp/scripts/test-mp-safe-area-and-state-polish.cjs`

**Step 1: 对齐查询行为**

- `GET /api/admin/chat-logs/users`
- `GET /api/admin/chat-logs?skip=&limit=&user_id=&search=`
- 保持 super admin 才能看到数据；前端只负责展示空数组/无权限状态

**Step 2: 完成小程序阅读体验**

- 用户筛选横向滚动
- 日志列表纵向滚动
- 翻页按钮、搜索确认、时间格式化、空状态

**Step 3: 处理 H5 与 MP 差异**

- H5 可保留 markdown 渲染
- 小程序先用纯文本展示，确保行为一致优先于富文本效果

**Step 4: 回归验证**

Run: `npm run test:chat-logs-mp-mvp`
Expected: PASS

### Task 5: 完成知识库上传闭环（前端适配，不改后端）

**Files:**
- Modify: `frontend-uniapp/src/pages/admin/admin.vue`
- Reference: `backend/routers/upload.py`
- Reference: `frontend/src/views/AdminView` 或现有 H5 上传逻辑
- Test: `frontend-uniapp/scripts/test-admin-upload-polling.cjs`
- Test: `frontend-uniapp/scripts/test-admin-mp-shell.cjs`

**Step 1: 锁定接口**

- `POST /api/upload/document?category=admin|biz&async_mode=true`
- `GET /api/upload/tasks/{task_id}`
- `GET /api/upload/documents?category=...`
- `DELETE /api/upload/document/{filename}`

**Step 2: 小程序端实现**

- 使用 `uni.chooseMessageFile` / `uni.uploadFile`（若当前环境允许）
- 上传后轮询 task 状态
- 展示 queued / processing / success / error
- 成功后刷新文件列表
- 删除后刷新列表

**Step 3: 保留 H5 现有上传行为**

- 不破坏 PC 端上传逻辑
- H5 与 MP 分支分离

### Task 6: 完整联调与迁移验收

**Files:**
- Verify: `frontend-uniapp/src/pages/admin/*.vue`
- Verify: `frontend-uniapp/src/pages/chat/chat.vue`
- Verify: `frontend-uniapp/src/pages/login/login.vue`
- Verify: `frontend-uniapp/.env.local`

**Step 1: 跑核心脚本**

Run: `npm run test:mp-core-smoke`
Expected: PASS

Run: `npm run build:mp-weixin`
Expected: PASS

**Step 2: 微信开发者工具联调**

- 验证登录
- 验证 Lab 设置读取/保存
- 验证 Staff CRUD
- 验证 Chat Logs 查询
- 验证知识库上传、列表、删除

**Step 3: 真机前置说明**

- 明确合法域名、HTTPS、真机调试约束
- 不因小程序网络限制修改后端接口语义

