# 小易恢复标准与 Smoke Case Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把“小易”的核心行为约束沉淀到项目文档里，并补一组固定 smoke case，覆盖最容易在 refactor 中被改丢的关键链路。

**Architecture:** 文档放到 `docs/operations/`，作为项目内唯一真源；smoke case 放到 `backend/tests/`，用 `unittest + TestClient` 固定关键用户场景，避免只靠 Prompt 口头约束。高风险规则优先做成接口级断言，风格类规则至少做成 prompt/response 关键字断言。

**Tech Stack:** Markdown, FastAPI TestClient, unittest

---

### Task 1: 沉淀“小易恢复标准”文档

**Files:**
- Create: `docs/operations/xiaoyi-recovery-standard.md`

**Step 1: 梳理规则分组**

按全局身份、报价、地址、知识库、教练、专家、社交、图片查单分组。

**Step 2: 写清“硬约束”和“风格约束”**

硬约束写成可验证条目；风格约束写成对实现与测试的期望。

**Step 3: 写清验证方式**

在文档里补 `smoke case` 跑法和维护要求。

### Task 2: 固定关键 smoke case

**Files:**
- Create: `backend/tests/test_xiaoyi_smoke_cases.py`

**Step 1: 先写失败测试**

覆盖至少以下场景：
- 报价：`200kg + ONT8`
- 知识库：公司介绍/能力介绍
- 教练模式：沉浸买家和禁止泄露同行名
- 专家模式：两轮问诊协议
- 社交闲聊：轻量响应
- 图片查单：补单号提醒

**Step 2: 运行测试确认红灯**

Run: `python -m unittest backend.tests.test_xiaoyi_smoke_cases`

Expected: FAIL

**Step 3: 写最小实现或复用现有实现**

尽量复用已经拆出的 service 和 router，不新建重复逻辑。

**Step 4: 重新跑测试**

Run: `python -m unittest backend.tests.test_xiaoyi_smoke_cases`

Expected: PASS

### Task 3: 整组回归

**Files:**
- Verify only

**Step 1: 跑 smoke case + 相关回归**

Run: `python -m unittest backend.tests.test_xiaoyi_smoke_cases backend.tests.test_quote_service backend.tests.test_chat_stream_regressions backend.tests.test_chat_mode_service backend.tests.test_chat_document_service`

**Step 2: 跑语法编译**

Run: `python -m py_compile backend/routers/chat.py backend/services/chat_document_service.py backend/services/chat_message_service.py backend/services/chat_mode_service.py backend/services/quote_service.py`
