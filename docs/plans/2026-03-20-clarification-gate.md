# 模糊问题追问 Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让小易在收到明显模糊、或缺少关键字段的问题时，先追问一轮再回答，降低答非所问。

**Architecture:** 在 `chat_intelligence.py` 中新增“按意图判断是否需要追问”的纯函数，并生成对应的追问文案；`chat.py` 只负责在意图识别之后调用该函数，命中时走现有的预构建流式响应出口。这样规则集中、可测试，也便于后续接 GLM5 时复用。

**Tech Stack:** FastAPI, Python service layer, unittest-based regression tests

---

### Task 1: 为模糊问题追问补充失败测试

**Files:**
- Modify: `backend/tests/test_chat_intelligence.py`

**Step 1: Write the failing test**

新增测试覆盖：
- 报价问题缺少仓库/区域/重量时，会要求用户补充关键信息。
- 地址问题只有“偏远吗/这个呢”之类模糊问法时，会要求用户补充邮编、仓库代码或完整地址。
- 已经具备关键字段的报价问题，不应被多余追问。

**Step 2: Run test to verify it fails**

Run: `backend\\venv\\Scripts\\python.exe backend\\tests\\test_chat_intelligence.py`
Expected: FAIL，因为通用追问逻辑尚未实现。

### Task 2: 实现通用追问判断与文案生成

**Files:**
- Modify: `backend/services/chat_intelligence.py`

**Step 1: Write minimal implementation**

新增：
- `build_intent_clarification_message`
- `should_ask_quote_clarification`
- `should_ask_address_clarification`

规则保持保守：
- 只在明显模糊或明显缺字段时追问。
- 文档场景继续沿用现有短句追问逻辑。

**Step 2: Run test to verify it passes**

Run: `backend\\venv\\Scripts\\python.exe backend\\tests\\test_chat_intelligence.py`
Expected: PASS

### Task 3: 接入聊天主流程并回归验证

**Files:**
- Modify: `backend/routers/chat.py`
- Test: `backend/tests/test_chat_intelligence.py`

**Step 1: Wire the new gate**

在意图识别完成后，统一调用 `build_intent_clarification_message`。如果返回非空文案，就让小易先追问一轮。

**Step 2: Run targeted verification**

Run:
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_chat_intelligence.py`
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_router_module_integrity.py`

Expected: PASS
