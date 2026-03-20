# 小程序设置功能对齐 Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让 `frontend-uniapp` 与 Web 端保持一致，补齐用户设置入口、输出长度偏好持久化与 Prompt 注入，以及当前用户修改密码功能。

**Architecture:** 在小程序聊天页 `chat.vue` 中新增一个轻量设置弹层，复用现有侧栏按钮与 `overlay + sheet` 交互模式。输出长度偏好通过 `uni.getStorageSync` / `uni.setStorageSync` 存储，并在聊天请求发送前注入前缀；密码修改逻辑放进 `auth` store，便于页面调用且兼容 H5/MP。

**Tech Stack:** uni-app, Vue 3 `<script setup>`, Pinia, uni storage API, uni.request / axios

---

### Task 1: 为小程序设置功能补充失败检查

**Files:**
- Create: `frontend-uniapp/scripts/test-chat-settings-sync.cjs`
- Modify: `frontend-uniapp/package.json`

**Step 1: Write the failing test**

检查以下关键片段：
- 聊天页存在设置入口与设置弹层
- 存在输出长度存储 key 与消息前缀注入
- auth store 存在修改密码 action 和 `/api/auth/change-password` 调用

**Step 2: Run test to verify it fails**

Run: `npm run test:chat-settings-sync`
Expected: FAIL，因为这些片段尚未全部存在。

### Task 2: 接入输出长度偏好与设置弹层

**Files:**
- Modify: `frontend-uniapp/src/pages/chat/chat.vue`

**Step 1: Write minimal implementation**

实现：
- 侧栏新增“设置”按钮
- 新增设置弹层
- 输出长度三档偏好
- 使用 `uni.setStorageSync` 持久化
- `sendMessage` 注入偏好前缀

**Step 2: Run test to verify it passes**

Run: `npm run test:chat-settings-sync`
Expected: PARTIAL PASS 或继续因密码逻辑缺失失败。

### Task 3: 接入密码修改能力

**Files:**
- Modify: `frontend-uniapp/src/store/auth.js`
- Modify: `frontend-uniapp/src/pages/chat/chat.vue`

**Step 1: Write minimal implementation**

实现：
- `auth.changePassword(oldPassword, newPassword)`
- 设置弹层中的当前密码、新密码、确认新密码表单
- 成功/失败 toast 反馈

**Step 2: Run test to verify it passes**

Run: `npm run test:chat-settings-sync`
Expected: PASS

### Task 4: 做一次定向回归

**Files:**
- Verify only

**Step 1: Run focused regression**

Run:
- `npm run test:chat-settings-sync`
- `npm run test:chat-page-bindings`
- `npm run test:auth-permissions-sync`

Expected: PASS
