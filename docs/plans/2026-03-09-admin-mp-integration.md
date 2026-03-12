# 管理台小程序联调 Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 打通小程序管理台的账号管理与实验室配置核心逻辑，并补上对应的 smoke coverage。

**Architecture:** 先用测试锁定小程序端需要具备的交互与请求分支，再补齐 `staff.vue` 的 CRUD/组织管理能力，同时修复后端 `staff` 路由的权限漏洞，最后增强 `lab.vue` 的加载与保存状态并纳入总 smoke。前端继续复用现有 `uni.request` + `resolveApiUrl` 方案，后端保持 FastAPI + SQLAlchemy 现有接口结构。

**Tech Stack:** Uni-app (Vue 3), Pinia, FastAPI, SQLAlchemy, Node `.cjs` smoke scripts, pytest

---

### Task 1: 规划与测试先行

**Files:**
- Create: `frontend-uniapp/scripts/test-staff-mp-crud.cjs`
- Create: `frontend-uniapp/scripts/test-lab-mp-state.cjs`
- Modify: `frontend-uniapp/scripts/test-mp-core-smoke.cjs`

**Step 1: Write the failing test**

编写两个新的 smoke 脚本：
- `test-staff-mp-crud.cjs`：检查小程序端 `staff.vue` 是否包含新增/编辑/删除账号、组织结构管理、对应的 `POST/PATCH/DELETE` 请求分支。
- `test-lab-mp-state.cjs`：检查 `lab.vue` 是否包含加载状态、脏状态/同步状态或保存反馈。

**Step 2: Run test to verify it fails**

Run: `npm run test:staff-mp-crud`
Expected: FAIL because current `staff.vue` only supports read-only listing.

Run: `npm run test:lab-mp-state`
Expected: FAIL because current `lab.vue` lacks stronger state handling.

**Step 3: Wire smoke runner**

把两个新脚本加入 `test-mp-core-smoke.cjs` 的 `localCommands`，保证后续总 smoke 会覆盖这轮联调。

**Step 4: Run test to verify it still fails correctly**

Run: `node scripts/test-mp-core-smoke.cjs`
Expected: FAIL at the new checks before implementation.

### Task 2: 修补后台 staff 权限边界

**Files:**
- Create: `backend/tests/test_staff_permissions.py`
- Modify: `backend/routers/staff.py`

**Step 1: Write the failing test**

新增后端测试，覆盖以下行为：
- `branch_admin` 不能把本分公司用户升级为 `super_admin`
- `branch_admin` 不能把用户改到其他分公司
- `branch_admin` 不能把其他分公司用户降维修改回来

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_staff_permissions.py -q`
Expected: FAIL because current `update_user` only校验目标用户当前所属分公司。

**Step 3: Write minimal implementation**

在 `backend/routers/staff.py` 中补齐 `update_user` 的权限规则：
- 分公司管理员只能在本分公司内操作
- 分公司管理员只能分配 `user` 或 `branch_admin`
- 分公司管理员不能改写 `branch_id` 到其他分公司

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_staff_permissions.py -q`
Expected: PASS

### Task 3: 实现小程序账号管理 CRUD 与组织管理

**Files:**
- Modify: `frontend-uniapp/src/pages/admin/staff.vue`

**Step 1: Write the failing test**

依赖 Task 1 的 `test-staff-mp-crud.cjs`，确保它明确检查：
- 新增账号入口
- 编辑与删除按钮
- 用户表单状态
- `requestStaff('/api/staff/users', { method: 'POST' ... })`
- `requestStaff('/api/staff/users/${...}', { method: 'PATCH' ... })`
- `requestStaff('/api/staff/users/${...}', { method: 'DELETE' ... })`
- 分公司/部门新增请求

**Step 2: Run test to verify it fails**

Run: `npm run test:staff-mp-crud`
Expected: FAIL

**Step 3: Write minimal implementation**

在 `staff.vue` 小程序分支中加入：
- 顶部操作区与新增账号入口
- 用户编辑表单卡片
- 分公司/部门管理卡片
- 保存、删除、刷新数据逻辑
- 基于当前角色的字段限制和按钮显隐

**Step 4: Run test to verify it passes**

Run: `npm run test:staff-mp-crud`
Expected: PASS

### Task 4: 增强小程序实验室配置状态

**Files:**
- Modify: `frontend-uniapp/src/pages/admin/lab.vue`

**Step 1: Write the failing test**

依赖 Task 1 的 `test-lab-mp-state.cjs`，要求页面具备：
- 加载态
- 保存成功/失败反馈
- 配置变更后的待保存状态或同步状态提示

**Step 2: Run test to verify it fails**

Run: `npm run test:lab-mp-state`
Expected: FAIL

**Step 3: Write minimal implementation**

在 `lab.vue` 中补充：
- `loading` / `syncStatus` / `lastSyncedAt`
- 初次拉取与保存后的状态更新
- 小程序端更清晰的状态文案与按钮禁用条件

**Step 4: Run test to verify it passes**

Run: `npm run test:lab-mp-state`
Expected: PASS

### Task 5: 全量回归

**Files:**
- Modify: `frontend-uniapp/package.json`
- Modify: `frontend-uniapp/scripts/test-mp-core-smoke.cjs`

**Step 1: Run focused tests**

Run: `npm run test:staff-mp-crud`
Expected: PASS

Run: `npm run test:lab-mp-state`
Expected: PASS

Run: `python -m pytest backend/tests/test_staff_permissions.py -q`
Expected: PASS

**Step 2: Run smoke bundle**

Run: `npm run test:mp-core-smoke`
Expected: PASS or only skip integration checks when backend is unreachable.

**Step 3: Run build verification**

Run: `npm run build:mp-weixin`
Expected: PASS

**Step 4: Commit (Use Chinese for commit message)**

```bash
git add docs/plans/2026-03-09-admin-mp-integration.md backend/routers/staff.py backend/tests/test_staff_permissions.py frontend-uniapp/src/pages/admin/staff.vue frontend-uniapp/src/pages/admin/lab.vue frontend-uniapp/scripts/test-staff-mp-crud.cjs frontend-uniapp/scripts/test-lab-mp-state.cjs frontend-uniapp/scripts/test-mp-core-smoke.cjs frontend-uniapp/package.json
git commit -m "feat: 打通小程序管理台核心联调"
```
