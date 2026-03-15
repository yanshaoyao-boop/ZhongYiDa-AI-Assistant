# 教练出题模式 Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 H5、小程序和后端中新增“教练出题”能力，支持上传单选题题库，并让用户按 5 / 10 / 20 题进入单题卡片式即时判题流程。

**Architecture:** 保留现有“教练对练”链路不动，在教练模式下新增一个并行的“教练出题”分支。后端新增独立题库接口与抽题接口，管理员上传题库文件后写入 JSON 数据文件；H5 与小程序前端复用现有教练模式入口，但切换为卡片式答题流和结果总结页。

**Tech Stack:** FastAPI、pandas、openpyxl、Vue 3、uni-app、Node CJS 静态回归脚本、Python unittest

---

### Task 1: 后端题库接口

**Files:**
- Create: `backend/routers/coach_quiz.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_coach_quiz.py`

**Step 1: Write the failing test**

编写测试覆盖：
- 管理员上传题库文件后能返回导入数量
- 普通登录用户能按题量获取随机题集
- 抽题接口不会返回超过题库总量的重复题
- 管理员能查看和删除题库题目

**Step 2: Run test to verify it fails**

Run: `python -m unittest backend.tests.test_coach_quiz -v`

Expected: FAIL，因为路由与解析逻辑尚不存在。

**Step 3: Write minimal implementation**

实现：
- `POST /api/coach-quiz/bank`
- `GET /api/coach-quiz/bank`
- `DELETE /api/coach-quiz/bank/{question_id}`
- `GET /api/coach-quiz/session?count=5`

题库文件先支持 `.xlsx`、`.xls`、`.csv`，列名按：
- `question`
- `option_a`
- `option_b`
- `option_c`
- `option_d`
- `answer`
- `explanation`
- `category`

**Step 4: Run test to verify it passes**

Run: `python -m unittest backend.tests.test_coach_quiz -v`

Expected: PASS

### Task 2: H5 教练模式新增“教练出题”

**Files:**
- Modify: `frontend/src/views/ChatView.vue`
- Test: `frontend/scripts/test-coach-quiz-mode.cjs`

**Step 1: Write the failing test**

编写静态回归脚本，检查：
- 教练模式存在“教练对练 / 教练出题”双入口
- 出题模式存在 `5 / 10 / 20` 题量入口
- 单题卡片区域、即时结果状态、总结卡片状态存在
- 出题模式开启时聊天输入区会隐藏或停用

**Step 2: Run test to verify it fails**

Run: `node scripts/test-coach-quiz-mode.cjs`

Expected: FAIL，因为模板与状态尚未补齐。

**Step 3: Write minimal implementation**

实现：
- 教练模式首页加入双入口卡片
- “教练出题”下加入题量选择卡片
- 进入后展示单题卡片、选项按钮、即时对错反馈、下一题按钮
- 最后一题完成后展示总结卡片与重新开始按钮

**Step 4: Run test to verify it passes**

Run: `node scripts/test-coach-quiz-mode.cjs`

Expected: PASS

### Task 3: 小程序教练模式新增“教练出题”

**Files:**
- Modify: `frontend-uniapp/src/pages/chat/chat.vue`
- Test: `frontend-uniapp/scripts/test-coach-quiz-mode.cjs`

**Step 1: Write the failing test**

编写静态回归脚本，检查：
- 教练模式存在出题入口
- 题量选择按钮存在
- 单题卡片、结果反馈、总结卡片结构存在
- 出题模式时不再显示普通聊天输入区

**Step 2: Run test to verify it fails**

Run: `node scripts/test-coach-quiz-mode.cjs`

Expected: FAIL

**Step 3: Write minimal implementation**

实现与 H5 对齐的小程序版本交互，但遵循现有 uni-app 视觉语言。

**Step 4: Run test to verify it passes**

Run: `node scripts/test-coach-quiz-mode.cjs`

Expected: PASS

### Task 4: H5 后台新增题库上传区

**Files:**
- Modify: `frontend/src/views/AdminView.vue`
- Test: `frontend/scripts/test-admin-coach-quiz-bank.cjs`

**Step 1: Write the failing test**

检查后台存在：
- “教练出题题库”上传区
- 上传按钮
- 已上传题目列表
- 删除题目入口

**Step 2: Run test to verify it fails**

Run: `node scripts/test-admin-coach-quiz-bank.cjs`

Expected: FAIL

**Step 3: Write minimal implementation**

复用现有上传器，接入新后端题库接口。

**Step 4: Run test to verify it passes**

Run: `node scripts/test-admin-coach-quiz-bank.cjs`

Expected: PASS

### Task 5: 小程序后台新增题库上传区

**Files:**
- Modify: `frontend-uniapp/src/pages/admin/admin.vue`
- Test: `frontend-uniapp/scripts/test-admin-coach-quiz-bank.cjs`

**Step 1: Write the failing test**

检查题库上传入口、题目列表与删除入口。

**Step 2: Run test to verify it fails**

Run: `node scripts/test-admin-coach-quiz-bank.cjs`

Expected: FAIL

**Step 3: Write minimal implementation**

沿用当前小程序后台的知识库管理卡片样式，新增题库分区。

**Step 4: Run test to verify it passes**

Run: `node scripts/test-admin-coach-quiz-bank.cjs`

Expected: PASS

### Task 6: 全量验证

**Files:**
- Verify: `backend/tests/test_coach_quiz.py`
- Verify: `frontend/scripts/test-coach-quiz-mode.cjs`
- Verify: `frontend/scripts/test-admin-coach-quiz-bank.cjs`
- Verify: `frontend-uniapp/scripts/test-coach-quiz-mode.cjs`
- Verify: `frontend-uniapp/scripts/test-admin-coach-quiz-bank.cjs`

**Step 1: Run backend verification**

Run: `python -m unittest backend.tests.test_coach_quiz -v`

**Step 2: Run H5 verification**

Run:
- `node scripts/test-coach-quiz-mode.cjs`
- `node scripts/test-admin-coach-quiz-bank.cjs`
- `npm run build`

Workdir: `frontend`

**Step 3: Run miniapp verification**

Run:
- `node scripts/test-coach-quiz-mode.cjs`
- `node scripts/test-admin-coach-quiz-bank.cjs`

Workdir: `frontend-uniapp`
