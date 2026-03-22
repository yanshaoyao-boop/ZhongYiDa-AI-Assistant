# Backend Chat Refactor Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不改变现有 `/api/chat/stream` 接口契约的前提下，拆分 `chat.py` 的后端编排逻辑，并加固轨迹查询异常处理。

**Architecture:** 先用回归测试锁住 intent、消息编排、轨迹等待逻辑，再把 `chat.py` 中可独立的职责迁移到 `services`。路由层继续负责 HTTP 入口和流式返回，业务判断、上下文构造和运行时防护下沉到独立 service。

**Tech Stack:** FastAPI, unittest/pytest, Playwright, SQLAlchemy

---

### Task 1: 抽离 Intent Service

**Files:**
- Create: `backend/services/chat_intent_service.py`
- Modify: `backend/routers/chat.py`
- Test: `backend/tests/test_chat_intent_service.py`

**Step 1: Write the failing test**

验证 `classify_intent` 对报价、偏远地址、轨迹号和上下文继承的行为。

**Step 2: Run test to verify it fails**

Run: `backend\\venv\\Scripts\\python -m pytest backend/tests/test_chat_intent_service.py -q`

Expected: FAIL，因为 `services.chat_intent_service` 不存在。

**Step 3: Write minimal implementation**

将正则、关键词和 `classify_intent` 从 `chat.py` 提取到 `chat_intent_service.py`。

**Step 4: Run test to verify it passes**

Run: `backend\\venv\\Scripts\\python -m pytest backend/tests/test_chat_intent_service.py -q`

Expected: PASS

### Task 2: 抽离消息编排 Service

**Files:**
- Create: `backend/services/chat_message_service.py`
- Modify: `backend/routers/chat.py`
- Test: `backend/tests/test_chat_message_service.py`

**Step 1: Write the failing test**

验证历史消息过滤、最大上下文裁剪、图片提示附加和全局风格 prompt 判断。

**Step 2: Run test to verify it fails**

Run: `backend\\venv\\Scripts\\python -m pytest backend/tests/test_chat_message_service.py -q`

Expected: FAIL，因为 `services.chat_message_service` 不存在。

**Step 3: Write minimal implementation**

提取 `wants_detailed_answer`、`build_global_style_prompt`、`build_model_messages`。

**Step 4: Run test to verify it passes**

Run: `backend\\venv\\Scripts\\python -m pytest backend/tests/test_chat_message_service.py -q`

Expected: PASS

### Task 3: 加固 Tracking Service

**Files:**
- Modify: `backend/services/tracking_service.py`
- Test: `backend/tests/test_tracking_service.py`

**Step 1: Write the failing test**

验证等待结果区域时仅吞掉可预期的 Playwright timeout，不吞掉其他异常。

**Step 2: Run test to verify it fails**

Run: `backend\\venv\\Scripts\\python -m pytest backend/tests/test_tracking_service.py -q`

Expected: FAIL，因为缺少等待辅助函数。

**Step 3: Write minimal implementation**

新增等待辅助函数并替换裸 `except:`。

**Step 4: Run test to verify it passes**

Run: `backend\\venv\\Scripts\\python -m pytest backend/tests/test_tracking_service.py -q`

Expected: PASS

### Task 4: 清理临时源码替换脚本

**Files:**
- Modify: `backend/scripts/fix_chat_logic.py`
- Optional Create: `backend/scripts/README.md`

**Step 1: 明确脚本用途**

将脚本标记为 deprecated，避免继续用于核心源码替换。

**Step 2: 保守清理**

保留历史参考价值，但让默认行为变成显式退出或说明。

### Task 5: 全量验证

**Files:**
- Verify only

**Step 1: Run targeted tests**

Run: `backend\\venv\\Scripts\\python -m pytest backend/tests/test_chat_intent_service.py backend/tests/test_chat_message_service.py backend/tests/test_tracking_service.py backend/tests/test_chat_intelligence.py backend/tests/test_router_module_integrity.py -q`

**Step 2: Run router compile guard**

Run: `backend\\venv\\Scripts\\python -m pytest backend/tests/test_router_module_integrity.py -q`

**Step 3: Run backend lint on touched files**

Run: `backend\\venv\\Scripts\\python -m ruff check backend/routers/chat.py backend/services/chat_intent_service.py backend/services/chat_message_service.py backend/services/tracking_service.py backend/tests/test_chat_intent_service.py backend/tests/test_chat_message_service.py backend/tests/test_tracking_service.py`

Plan complete and saved to `docs/plans/2026-03-20-backend-chat-refactor.md`.
