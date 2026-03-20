# 知识库上传与索引优化 Implementation Plan (中文)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 优化管理后台上传材料链路，解决同名文档冲突、让 `admin/biz` 分类真正参与检索，并降低 PDF 视觉解析的无效成本。

**Architecture:** 上传层把文档按分类落盘，并在向量库中为每份文档写入稳定的 `source_key`，删除时按分类精准删除。检索层新增轻量分类推断，把明显属于行政或业务材料的问题优先限定到对应类别。解析层新增 PDF 视觉门控，只在页面文本不足时才调用视觉模型，避免把装饰图片和已有可提取文本的页面重复送模。

**Tech Stack:** FastAPI, Python service layer, ChromaDB, unittest-based regression tests, Vue admin frontend

---

### Task 1: 为上传分类隔离与检索分类推断补充失败测试

**Files:**
- Modify: `backend/tests/test_upload_tasks.py`
- Modify: `backend/tests/test_chat_intelligence.py`
- Create: `backend/tests/test_doc_parser.py`

**Step 1: Write the failing test**

覆盖以下行为：
- 同名文件分别上传到 `admin` 和 `biz` 时，会落到不同目录，不再互相覆盖。
- 知识库问题能推断为 `admin` / `biz` / `None`。
- PDF 页面已有足够文本时，不应触发视觉解析。

**Step 2: Run test to verify it fails**

Run:
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_upload_tasks.py`
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_chat_intelligence.py`
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_doc_parser.py`

Expected: FAIL，说明优化点还未实现。

### Task 2: 实现分类安全的上传与删除

**Files:**
- Modify: `backend/routers/upload.py`
- Modify: `frontend/src/views/AdminView.vue`

**Step 1: Write minimal implementation**

实现：
- 文档按分类写入 `docs/admin`、`docs/biz`
- metadata 写入 `source_key`
- 删除接口支持按分类精准删除
- 前端删除按钮把分类带回后端

**Step 2: Run targeted tests**

Run: `backend\\venv\\Scripts\\python.exe backend\\tests\\test_upload_tasks.py`
Expected: PASS

### Task 3: 实现分类感知检索与 PDF 视觉门控

**Files:**
- Modify: `backend/services/chat_intelligence.py`
- Modify: `backend/routers/chat.py`
- Modify: `backend/services/doc_parser.py`

**Step 1: Write minimal implementation**

实现：
- `infer_knowledge_category`
- 聊天检索时把推断出的类别传给 RAG 查询
- `should_use_pdf_vision`
- PDF 仅在页面文本过少且存在图片时才调用视觉模型

**Step 2: Run targeted tests**

Run:
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_chat_intelligence.py`
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_doc_parser.py`
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_router_module_integrity.py`

Expected: PASS

### Task 4: 做一次定向回归

**Files:**
- Verify only

**Step 1: Run focused regression**

Run:
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_upload_tasks.py`
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_chat_intelligence.py`
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_doc_parser.py`
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_chat_image_uploads.py`
- `backend\\venv\\Scripts\\python.exe backend\\tests\\test_router_module_integrity.py`

Expected: PASS
