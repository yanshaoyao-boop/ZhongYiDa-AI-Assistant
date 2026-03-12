# 小程序真后端联调与真机验收 Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不修改 `backend` 业务逻辑的前提下，完成 `frontend-uniapp` 对现有后端的真实联调、跨端一致性核对与真机验收，确认小程序版小易可作为微信端外壳稳定使用。

**Architecture:** 以后端为冻结基线，只校验接口可达性、鉴权、流式聊天、上传与后台管理链路是否与老 H5 一致。前端优先修正 `frontend-uniapp` 的接口配置、状态处理和微信环境兼容；凡是联调中出现“必须改后端”的点，一律先记录为阻塞，不直接实现。

**Tech Stack:** uni-app, Vue 3, Pinia, Weixin Mini Program Devtools, FastAPI, Axios/uni.request, 微信真机调试

---

### Task 1: 准备联调环境与基线记录

**Files:**
- Verify: `backend/.env`
- Verify: `backend/main.py`
- Verify: `frontend-uniapp/.env.local`
- Verify: `frontend-uniapp/src/utils/api.js`
- Verify: `frontend-uniapp/src/store/auth.js`
- Reference: `frontend/src/views/ChatView.vue`

**Step 1: 记录当前本地 IP 与后端访问地址**

Run: `ipconfig`
Expected: 能看到当前开发机局域网 IPv4 地址，例如 `192.168.x.x`

**Step 2: 启动后端服务**

Run: `python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
Workdir: `backend`
Expected: 本机与局域网内可访问 `http://<LAN_IP>:8000/docs`

**Step 3: 确认小程序 API Base 配置**

- 检查 `frontend-uniapp/.env.local` 是否指向 `http://<LAN_IP>:8000`
- 检查 `frontend-uniapp/src/utils/api.js` 是否会优先读取存储中的 `zyd_api_base_url`
- 如小程序已缓存旧地址，手动清空 Storage 或在登录前重写 API Base

**Step 4: 跑一次基础 smoke，作为联调前基线**

Run: `npm run test:mp-core-smoke`
Workdir: `frontend-uniapp`
Expected: PASS；若 integration smoke 仍提示 backend unreachable，记录为“环境未连通”

### Task 2: 微信开发者工具联调登录、鉴权与退出

**Files:**
- Verify: `frontend-uniapp/src/pages/login/login.vue`
- Verify: `frontend-uniapp/src/store/auth.js`
- Verify: `frontend-uniapp/src/utils/api.js`
- Verify: `frontend-uniapp/src/pages/chat/chat.vue`

**Step 1: 导入小程序构建产物**

Run: `npm run build:mp-weixin`
Workdir: `frontend-uniapp`
Expected: PASS，并生成 `frontend-uniapp/dist/build/mp-weixin`

**Step 2: 在微信开发者工具中打开项目**

- 导入目录：`frontend-uniapp/dist/build/mp-weixin`
- 关闭“使用本地服务代理”等额外干扰项
- 确认小程序启动进入登录页

**Step 3: 验证登录成功链路**

- 输入有效账号密码
- 预期：拿到 token，跳转到聊天页，`Storage` 中写入 token 与用户信息
- 若失败，先在开发者工具 Network 中确认请求 URL、请求头、响应码

**Step 4: 验证鉴权失败与退出**

- 手动删掉 token 后重新进入后台页
- 预期：被重定向或拦截到登录
- 点击退出登录
- 预期：清空本地 token/用户态并返回登录页

### Task 3: 联调聊天主链路

**Files:**
- Verify: `frontend-uniapp/src/pages/chat/chat.vue`
- Verify: `frontend-uniapp/src/utils/mp-stream-chat.js`
- Verify: `frontend-uniapp/src/utils/chat-image-upload.js`
- Verify: `frontend-uniapp/src/utils/error-logger.js`
- Reference: `backend/routers/chat.py`

**Step 1: 验证模式切换**

- 依次切换“全能助手 / 知识教练 / 专家指导”
- 预期：欢迎态、上下文提示、会话模式记忆与发送行为一致

**Step 2: 验证文本聊天与流式回复**

- 发一条普通问题
- 预期：出现用户消息、助手流式回复、可中途停止
- 若不是流式而是整段返回，检查 `mp-stream-chat.js` 是否命中了小程序分支

**Step 3: 验证会话管理**

- 新建会话
- 切换历史会话
- 删除会话
- 预期：本地缓存与当前展示一致，无空白态错乱

**Step 4: 验证图片上传与带图对话**

- 选择一张真实图片
- 预期：前端可预览、上传成功、消息附图、后端能收到图片内容
- 再发送“仅图片无文字”和“图片+文字”两种组合

**Step 5: 记录聊天链路问题清单**

- 按“必修 / 可后续优化”分组
- 必修：登录后无法发消息、流式断裂、图片上传失败、会话错乱
- 后续：欢迎态 polish、滚动体验、空态文案

### Task 4: 联调管理后台闭环

**Files:**
- Verify: `frontend-uniapp/src/pages/admin/admin.vue`
- Verify: `frontend-uniapp/src/pages/admin/lab.vue`
- Verify: `frontend-uniapp/src/pages/admin/staff.vue`
- Verify: `frontend-uniapp/src/pages/admin/chat-logs.vue`
- Reference: `backend/routers/upload.py`
- Reference: `backend/routers/staff.py`

**Step 1: 验证后台入口与权限**

- 使用 super admin 登录
- 进入“业务知识库 / 小易实验室 / 会话审计 / 账号管理”
- 预期：入口可进入，权限不足账号会被正确拦截

**Step 2: 验证知识库上传闭环**

- 分别上传：业务资料、行政资料、报价表、教练案例
- 预期：能看到上传进度、处理完成状态、上传后列表刷新、删除后列表刷新

**Step 3: 验证 Lab 配置页**

- 拉取配置
- 修改一项设置并保存
- 预期：显示 dirty / saving / saved 状态，刷新后值仍正确

**Step 4: 验证 Staff CRUD**

- 新增账号
- 编辑账号
- 删除非当前账号
- 新增 branch / department
- 预期：前端表单、列表刷新、错误提示都正常

**Step 5: 验证 Chat Logs**

- 查看用户筛选
- 搜索关键字
- 分页切换
- 预期：数据展示正常，非 super admin 账号正确受限

### Task 5: 跨端一致性核对

**Files:**
- Verify: `frontend/src/views/ChatView.vue`
- Verify: `frontend/src/views/AdminView.vue`
- Verify: `frontend/src/views/ChatLogsView.vue`
- Verify: `frontend-uniapp/src/pages/chat/chat.vue`
- Verify: `frontend-uniapp/src/pages/admin/*.vue`

**Step 1: 对照同一账号的聊天结果**

- 在老 H5 与小程序分别提同一问题
- 预期：命中同一后端、同一知识库、回复风格与上下文来源一致

**Step 2: 对照上传后的资料**

- 小程序上传一份资料后，到老 H5 查看是否可见
- 老 H5 上传一份资料后，到小程序查看是否可见
- 预期：列表一致

**Step 3: 对照聊天审计记录**

- 小程序发起一轮聊天
- 到老 H5 或后台看 chat logs
- 预期：能查到同一条会话记录

**Step 4: 单独列出仍属本地缓存的项**

- 例如：当前会话列表、本地模式记忆、未提交输入框内容
- 这些不作为本轮阻塞，但需记录为“后续跨端同步项”

### Task 6: 真机验收与阻塞清单

**Files:**
- Verify: `frontend-uniapp/src/pages/chat/chat.vue`
- Verify: `frontend-uniapp/src/pages/admin/*.vue`
- Verify: `frontend-uniapp/src/pages.json`
- Verify: `frontend-uniapp/src/manifest.json`

**Step 1: 真机验聊天体验**

- 测试刘海区、安全区、底部输入区、键盘顶起、滚动回弹
- 预期：无明显遮挡，无输入框漂移

**Step 2: 真机验上传体验**

- 测试相册/文件选择、图片预览、上传进度、失败重试
- 预期：状态可感知，失败有提示

**Step 3: 真机验后台操作**

- 用管理员账号在真机上完成一次上传、一次配置保存、一次 Staff 操作
- 预期：页面不卡死，交互可完成

**Step 4: 输出验收结论**

- A 类：已通过，可进入下一批
- B 类：前端可修，直接排进下一批
- C 类：疑似必须改后端，暂停并单独确认

**Step 5: Commit（Use Chinese for commit message）**

```bash
git add docs/plans/2026-03-12-miniapp-real-device-integration.md
git commit -m "docs: 补充小程序真后端联调与真机验收计划"
```
