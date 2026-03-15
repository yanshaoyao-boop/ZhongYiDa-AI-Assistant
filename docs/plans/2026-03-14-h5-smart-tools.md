# H5 智能工具迁移 Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 H5 版本新增“智能工具”分类入口，并把现有业务工具、行政工具以原 UI 迁移到小易系统中统一访问。

**Architecture:** 后端提供一份工具清单 API，并统一托管各工具的静态产物；H5 前端新增工具中心页面，按“业务工具 / 行政工具”分组展示并跳转到对应工具页面。优先复用现有工具源码或已生成产物，不重写工具 UI，不接入小程序。

**Tech Stack:** FastAPI、Vue 3、Vue Router、Vite、Python unittest

---

### Task 1: 工具目录 API 与静态托管

**Files:**
- Modify: `backend/main.py`
- Create: `backend/routers/tools.py`
- Test: `backend/tests/test_tools.py`

**Step 1: Write the failing test**

```python
def test_tools_catalog_returns_biz_and_admin_groups(self):
    response = self.client.get("/api/tools/")
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual([group["key"] for group in data["groups"]], ["business", "admin"])
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest backend.tests.test_tools -v`
Expected: FAIL，因为 `/api/tools/` 尚未存在。

**Step 3: Write minimal implementation**

```python
router = APIRouter(prefix="/api/tools", tags=["tools"])

@router.get("/")
def list_tools():
    return {"groups": TOOL_GROUPS}
```

同时在 `main.py` 挂载工具路由与静态目录。

**Step 4: Run test to verify it passes**

Run: `python -m unittest backend.tests.test_tools -v`
Expected: PASS

**Step 5: Commit (Use Chinese for commit message)**

```bash
git add backend/main.py backend/routers/tools.py backend/tests/test_tools.py
git commit -m "feat: 添加H5智能工具目录与静态托管"
```

### Task 2: H5 工具中心页面与路由

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/views/ChatView.vue`
- Create: `frontend/src/views/ToolsView.vue`

**Step 1: Write the failing test**

由于当前 H5 项目没有现成测试框架，本任务使用 build 作为最小验证门槛，并先确保路由引用存在。

**Step 2: Run test to verify it fails**

Run: `npm run build`
Workdir: `frontend`
Expected: FAIL，如果 `ToolsView.vue` 或新路由尚未实现。

**Step 3: Write minimal implementation**

```js
{
  path: '/tools',
  name: 'Tools',
  component: () => import('../views/ToolsView.vue'),
  meta: { requiresAuth: true }
}
```

在 `ChatView.vue` 将“智能工具”按钮接到 `/tools`，并在 `ToolsView.vue` 通过 `/api/tools/` 拉取数据，按业务工具、行政工具展示卡片列表。

**Step 4: Run test to verify it passes**

Run: `npm run build`
Workdir: `frontend`
Expected: PASS

**Step 5: Commit (Use Chinese for commit message)**

```bash
git add frontend/src/router/index.js frontend/src/views/ChatView.vue frontend/src/views/ToolsView.vue
git commit -m "feat: 添加H5智能工具中心页面"
```

### Task 3: 工具静态资源挂载与回归验证

**Files:**
- Modify: `backend/routers/tools.py`
- Create: `backend/data/tools/` 下的静态资源目录或映射
- Optional Modify: 与工具托管相关的脚本文件

**Step 1: Write the failing test**

```python
def test_tool_entry_points_are_resolvable(self):
    response = self.client.get("/tools/business/hepiao/")
    self.assertEqual(response.status_code, 200)
    self.assertIn("text/html", response.headers["content-type"])
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest backend.tests.test_tools -v`
Expected: FAIL，因为静态页面尚未挂上。

**Step 3: Write minimal implementation**

将已存在的工具产物或原始 HTML/构建结果放入后端可访问目录，为每个工具分配稳定 slug，并让 API 返回对应 URL。

**Step 4: Run test to verify it passes**

Run: `python -m unittest backend.tests.test_tools -v`
Expected: PASS

**Step 5: Commit (Use Chinese for commit message)**

```bash
git add backend/routers/tools.py backend/data/tools
git commit -m "feat: 挂载H5智能工具静态资源"
```

### Task 4: 端到端验证

**Files:**
- Verify only

**Step 1: Run backend tests**

Run: `python -m unittest backend.tests.test_tools -v`
Expected: PASS

**Step 2: Run frontend build**

Run: `npm run build`
Workdir: `frontend`
Expected: PASS

**Step 3: Sanity-check migrated tools**

Run: 启动后端后访问 `/tools` 和至少一个业务工具、一个行政工具页面，确认工具 UI 未被改写。

**Step 4: Commit (Use Chinese for commit message)**

```bash
git add .
git commit -m "feat: 迁移H5智能工具到小易"
```
