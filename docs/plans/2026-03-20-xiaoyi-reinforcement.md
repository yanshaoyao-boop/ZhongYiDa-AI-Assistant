# 小易强化 Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不等待 GLM5 接入的前提下，先提升小易的检索准确率、低置信度场景处理能力，以及内部知识回答的来源感。

**Architecture:** 新增一个纯函数服务层 `chat_intelligence.py`，把“查询改写、文档重排、来源摘要、低置信度追问”从 `chat.py` 中拆出来，便于单元测试和后续给 GLM5 复用。`chat.py` 只负责调用这些能力，并保持现有流式输出协议不变。

**Tech Stack:** FastAPI, pytest/unittest, Python services, ChromaDB-backed RAG

---

### Task 1: 为小易强化逻辑建立可测试的纯函数层

**Files:**
- Create: `backend/tests/test_chat_intelligence.py`
- Create: `backend/services/chat_intelligence.py`

**Step 1: Write the failing test**

编写测试覆盖以下行为：
- 短句文档追问会自动拼接最近有效上下文形成更强检索查询。
- 命中公司介绍类短问时，会自动补充公司简介扩展词。
- 文档重排会优先保留与查询关键词更相关的来源。
- 来源摘要会去重并输出简洁来源列表。
- 过于模糊的短句在缺少有效上下文时会触发澄清。

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_chat_intelligence.py -q`
Expected: FAIL，因为 `chat_intelligence.py` 还不存在。

**Step 3: Write minimal implementation**

在 `backend/services/chat_intelligence.py` 中实现：
- `build_document_search_query`
- `rerank_similar_documents`
- `summarize_document_sources`
- `should_ask_document_clarification`

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_chat_intelligence.py -q`
Expected: PASS

### Task 2: 将强化逻辑接入聊天主流程

**Files:**
- Modify: `backend/routers/chat.py`
- Test: `backend/tests/test_chat_intelligence.py`

**Step 1: Write the failing test**

先补充一个更贴近路由使用方式的测试，验证：
- 模糊短句会返回澄清文案。
- 文档查询会使用改写后的 `search_query`。
- 文档结果存在时会生成来源摘要字符串。

**Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_chat_intelligence.py -q`
Expected: FAIL，说明当前 `chat.py` 还未接入新逻辑。

**Step 3: Write minimal implementation**

在 `backend/routers/chat.py` 中：
- 在 `document` 分支里用 `build_document_search_query` 生成检索词。
- 在拿到 `similar_docs` 后调用 `rerank_similar_documents`。
- 在需要时直接返回澄清文案，避免硬答。
- 将来源摘要注入 system prompt，并在最终文本末尾追加 `参考来源`。

**Step 4: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_chat_intelligence.py -q`
Expected: PASS

### Task 3: 做一次定向回归验证

**Files:**
- Verify only

**Step 1: Run targeted tests**

Run:
- `python -m pytest backend/tests/test_chat_intelligence.py -q`
- `python -m pytest backend/tests/test_chat_image_uploads.py -q`
- `python -m pytest backend/tests/test_router_module_integrity.py -q`

Expected: PASS

**Step 2: 记录后续 GLM5 接入建议**

记录这轮强化已经把哪些逻辑前置到底层：
- 查询改写
- 文档重排
- 澄清门控
- 来源摘要

这样两天后 GLM5 接入时，只需要新增“复杂任务路由层”，不必重做底层检索。
