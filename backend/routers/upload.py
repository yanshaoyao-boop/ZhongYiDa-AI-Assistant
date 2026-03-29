import asyncio
import base64
import json
import os
import threading
import uuid
from datetime import datetime, timezone

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from dependencies import User, get_admin_user, get_current_user, has_permission
from services.doc_parser import chunk_text, parse_document
from services.llm_client import analyze_coach_case, get_embedding
from services.quote_service import DATA_DIR as QUOTE_DIR
from services.quote_service import load_all_quotes, parse_quote_file
from services.rag_service import add_documents_to_db, delete_documents_by_source, delete_documents_by_source_key
from services.rag_service import delete_legacy_untyped_documents_by_source

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "docs")
COACH_CASES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "coach_cases.json")
CHAT_IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chat_images")
MAX_CHAT_IMAGE_SIZE_BYTES = 8 * 1024 * 1024
os.makedirs(UPLOAD_DOCS_DIR, exist_ok=True)
os.makedirs(QUOTE_DIR, exist_ok=True)
os.makedirs(CHAT_IMAGE_DIR, exist_ok=True)

_coach_cases_lock = asyncio.Lock()
_UPLOAD_TASKS = {}
_UPLOAD_TASKS_LOCK = threading.Lock()
_CHAT_IMAGE_UPLOADS = {}
_CHAT_IMAGE_UPLOADS_LOCK = threading.Lock()
DOCUMENT_CATEGORIES = {"admin", "biz"}


def _normalize_document_category(category: str | None) -> str:
    if category in DOCUMENT_CATEGORIES:
        return str(category)
    return "biz"


def _get_docs_category_dir(category: str | None) -> str:
    normalized = _normalize_document_category(category)
    category_dir = os.path.join(UPLOAD_DOCS_DIR, normalized)
    os.makedirs(category_dir, exist_ok=True)
    return category_dir


def _get_document_file_path(category: str | None, filename: str) -> str:
    return os.path.join(_get_docs_category_dir(category), filename)


def _build_source_key(category: str | None, filename: str) -> str:
    return f"{_normalize_document_category(category)}::{filename}"


def _task_timestamp():
    return datetime.now(timezone.utc).isoformat()


def _create_upload_task(filename: str, category: str):
    task_id = uuid.uuid4().hex
    task = {
        "task_id": task_id,
        "filename": filename,
        "category": category,
        "status": "queued",
        "stage": "queued",
        "message": "Queued for processing.",
        "error": "",
        "processed_chunks": 0,
        "total_chunks": 0,
        "created_at": _task_timestamp(),
        "updated_at": _task_timestamp(),
        "result": None,
    }
    with _UPLOAD_TASKS_LOCK:
        _UPLOAD_TASKS[task_id] = task
    return dict(task)


def _get_upload_task(task_id: str):
    with _UPLOAD_TASKS_LOCK:
        task = _UPLOAD_TASKS.get(task_id)
        return dict(task) if task else None


def _update_upload_task(task_id: str, **changes):
    with _UPLOAD_TASKS_LOCK:
        task = _UPLOAD_TASKS.get(task_id)
        if task is None:
            return None
        task.update(changes)
        task["updated_at"] = _task_timestamp()
        return dict(task)


def _create_chat_image_upload(filename: str, stored_filename: str, content_type: str, size: int):
    image_upload_id = uuid.uuid4().hex
    record = {
        "image_upload_id": image_upload_id,
        "filename": filename,
        "stored_filename": stored_filename,
        "file_path": os.path.join(CHAT_IMAGE_DIR, stored_filename),
        "content_type": content_type,
        "size": size,
        "created_at": _task_timestamp(),
    }
    with _CHAT_IMAGE_UPLOADS_LOCK:
        _CHAT_IMAGE_UPLOADS[image_upload_id] = record
    return dict(record)


def get_chat_image_upload(image_upload_id: str):
    with _CHAT_IMAGE_UPLOADS_LOCK:
        record = _CHAT_IMAGE_UPLOADS.get(image_upload_id)
        return dict(record) if record else None


def get_chat_image_base64(image_upload_id: str) -> str:
    record = get_chat_image_upload(image_upload_id)
    if record is None:
        raise FileNotFoundError("Chat image upload not found.")

    file_path = record["file_path"]
    if not os.path.exists(file_path):
        raise FileNotFoundError("Chat image file is missing.")

    with open(file_path, "rb") as handle:
        return base64.b64encode(handle.read()).decode("utf-8")


async def _process_document_file(file_path: str, safe_filename: str, category: str, task_id: str | None = None):
    if task_id:
        _update_upload_task(
            task_id,
            status="processing",
            stage="extracting",
            message="Extracting text from document.",
        )

    text = await parse_document(file_path)
    if not text.strip():
        raise ValueError("No text could be extracted from the document.")

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No chunks were generated from the document.")

    if task_id:
        _update_upload_task(
            task_id,
            status="processing",
            stage="chunking",
            message=f"Prepared {len(chunks)} chunks.",
            total_chunks=len(chunks),
            processed_chunks=0,
        )

    source_key = _build_source_key(category, safe_filename)
    await asyncio.to_thread(delete_documents_by_source_key, source_key)
    await asyncio.to_thread(delete_legacy_untyped_documents_by_source, safe_filename)

    batch_size = 5
    processed_chunks = 0

    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start:batch_start + batch_size]
        embeddings = await asyncio.gather(*[get_embedding(chunk) for chunk in batch])

        ids = [f"{safe_filename}_chunk_{batch_start + index}_{uuid.uuid4().hex[:8]}" for index in range(len(batch))]
        metadatas = [{"source": safe_filename, "source_key": source_key, "category": category}] * len(batch)

        await asyncio.to_thread(
            add_documents_to_db,
            ids=ids,
            texts=list(batch),
            embeddings=list(embeddings),
            metadatas=metadatas,
        )

        processed_chunks += len(batch)
        if task_id:
            _update_upload_task(
                task_id,
                status="processing",
                stage="embedding",
                message=f"Processed {processed_chunks}/{len(chunks)} chunks.",
                processed_chunks=processed_chunks,
                total_chunks=len(chunks),
            )

    return {
        "filename": safe_filename,
        "chunks": len(chunks),
        "message": f"Document {safe_filename} processed successfully. Extracted {len(chunks)} chunks.",
    }


async def _process_document_task(task_id: str, file_path: str, safe_filename: str, category: str):
    try:
        result = await _process_document_file(file_path, safe_filename, category, task_id=task_id)
        _update_upload_task(
            task_id,
            status="success",
            stage="completed",
            message=result["message"],
            error="",
            processed_chunks=result["chunks"],
            total_chunks=result["chunks"],
            result=result,
        )
    except Exception as error:
        _update_upload_task(
            task_id,
            status="error",
            stage="failed",
            message=str(error),
            error=str(error),
        )


def _schedule_document_processing(task_id: str, file_path: str, safe_filename: str, category: str):
    asyncio.create_task(_process_document_task(task_id, file_path, safe_filename, category))


@router.get("/tasks/{task_id}")
async def get_upload_task(
    task_id: str,
    admin: User = Depends(get_admin_user),
):
    task = _get_upload_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Upload task not found.")
    return task


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    category: str = "biz",
    async_mode: bool = False,
    admin: User = Depends(has_permission("edit_knowledge")),
):
    category = _normalize_document_category(category)
    safe_filename = os.path.basename(file.filename or "")
    file_path = _get_document_file_path(category, safe_filename)
    content = await file.read()

    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(content)

    if async_mode:
        task = _create_upload_task(safe_filename, category)
        _schedule_document_processing(task["task_id"], file_path, safe_filename, category)
        return task

    try:
        result = await _process_document_file(file_path, safe_filename, category)
        return {"status": "success", "message": result["message"]}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/quote")
async def upload_quote(
    file: UploadFile = File(...),
    admin: User = Depends(has_permission("edit_prices")),
):
    safe_filename = os.path.basename(file.filename or "")
    file_path = os.path.join(QUOTE_DIR, safe_filename)
    content = await file.read()

    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(content)

    try:
        data_list = await asyncio.to_thread(parse_quote_file, file_path)
        if not data_list:
            return {"status": "error", "message": "Failed to parse spreadsheet or file is empty."}

        await asyncio.to_thread(load_all_quotes)
        return {"status": "success", "message": f"Quote file {safe_filename} uploaded and parsed successfully."}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/chat-image")
async def upload_chat_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    content_type = str(file.content_type or "")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    safe_filename = os.path.basename(file.filename or "")
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Missing image filename.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    if len(content) > MAX_CHAT_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Image file is too large.")

    _, extension = os.path.splitext(safe_filename)
    stored_filename = f"{uuid.uuid4().hex}{extension.lower()}"
    file_path = os.path.join(CHAT_IMAGE_DIR, stored_filename)

    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(content)

    record = _create_chat_image_upload(
        filename=safe_filename,
        stored_filename=stored_filename,
        content_type=content_type,
        size=len(content),
    )
    return {
        "image_upload_id": record["image_upload_id"],
        "filename": record["filename"],
        "content_type": record["content_type"],
        "size": record["size"],
        "created_at": record["created_at"],
    }


@router.get("/documents")
async def list_documents(
    category: str = None,
    user: User = Depends(get_current_user),
):
    try:
        if category:
            category_dir = _get_docs_category_dir(category)
            if not os.path.exists(category_dir):
                return {"files": []}
            files = [name for name in os.listdir(category_dir) if os.path.isfile(os.path.join(category_dir, name))]
            files.sort(key=lambda name: os.path.getmtime(os.path.join(category_dir, name)), reverse=True)
        else:
            files = []
            for doc_category in sorted(DOCUMENT_CATEGORIES):
                category_dir = _get_docs_category_dir(doc_category)
                if not os.path.exists(category_dir):
                    continue
                files.extend(
                    name
                    for name in os.listdir(category_dir)
                    if os.path.isfile(os.path.join(category_dir, name))
                )
            files = sorted(set(files))
        return {"files": files}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.delete("/document/{filename}")
async def delete_document(
    filename: str,
    category: str = None,
    admin: User = Depends(has_permission("edit_knowledge")),
):
    try:
        safe_filename = os.path.basename(filename)
        categories = [_normalize_document_category(category)] if category else sorted(DOCUMENT_CATEGORIES)
        deleted_any = False
        for doc_category in categories:
            file_path = _get_document_file_path(doc_category, safe_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_any = True
            await asyncio.to_thread(delete_documents_by_source_key, _build_source_key(doc_category, safe_filename))

        if not deleted_any and category is None:
            await asyncio.to_thread(delete_documents_by_source, safe_filename)
        return {"status": "success", "message": f"Document {filename} deleted successfully."}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/quotes")
async def list_quotes(
    user: User = Depends(get_current_user),
):
    try:
        if not os.path.exists(QUOTE_DIR):
            return {"files": []}
        files = [name for name in os.listdir(QUOTE_DIR) if os.path.isfile(os.path.join(QUOTE_DIR, name))]
        files.sort(key=lambda name: os.path.getmtime(os.path.join(QUOTE_DIR, name)), reverse=True)
        return {"files": files}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.delete("/quote/{filename}")
async def delete_quote(
    filename: str,
    admin: User = Depends(has_permission("edit_prices")),
):
    try:
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(QUOTE_DIR, safe_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        load_all_quotes()
        return {"status": "success", "message": f"Quote file {filename} deleted successfully."}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/coach-case")
async def create_coach_case(
    file: UploadFile = File(...),
    admin: User = Depends(has_permission("edit_cases")),
):
    try:
        content = await parse_document_content(file)
        print(f">> Received file: {file.filename}, length: {len(content)}")

        import re

        case_blocks = re.split(r"(?=案例\s*\d+\s*[:：]?|\={5,})", content)

        case_texts = []
        for block in case_blocks:
            cleaned = re.sub(r"\={5,}", "", block.strip()).strip()
            if len(cleaned) > 20:
                case_texts.append(cleaned)

        print(f">> Found {len(case_texts)} potential cases in file.")

        new_cases = []
        batch_limit = 30
        for index, text in enumerate(case_texts[:batch_limit]):
            try:
                print(f">> Processing case {index + 1}/{min(len(case_texts), batch_limit)}...")
                case_data = await analyze_coach_case(text, hint=file.filename)
                print(f">> Successfully analyzed case: {case_data.get('name')}")
                case_data["id"] = uuid.uuid4().hex[:8]
                case_data["source"] = file.filename
                new_cases.append(case_data)
            except Exception as error:
                print(f"!! Error processing case block {index}: {error}")
                continue

        async with _coach_cases_lock:
            cases = []
            if os.path.exists(COACH_CASES_FILE):
                with open(COACH_CASES_FILE, "r", encoding="utf-8") as handle:
                    cases = json.load(handle)

            combined = new_cases + cases
            with open(COACH_CASES_FILE, "w", encoding="utf-8") as handle:
                json.dump(combined, handle, ensure_ascii=False, indent=2)

        print(f">> Successfully processed {len(new_cases)} cases.")
        note = ""
        if len(case_texts) > batch_limit:
            note = (
                f"为了保证分析质量，系统单次批量处理前 {batch_limit} 条。"
                "如有更多，请分批上传或联系管理员。"
            )

        return {
            "status": "success",
            "processed_count": len(new_cases),
            "total_found": len(case_texts),
            "note": note,
        }
    except Exception as error:
        print(f"!! Global error in create_coach_case: {error}")
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/coach-cases")
async def list_coach_cases(
    category: str = None,
    user: User = Depends(get_current_user),
):
    try:
        if not os.path.exists(COACH_CASES_FILE):
            return []
        with open(COACH_CASES_FILE, "r", encoding="utf-8") as handle:
            cases = json.load(handle)

        if category:
            return [case for case in cases if category in case.get("category", "")]
        return cases
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.delete("/coach-case/{case_id}")
async def delete_coach_case(
    case_id: str,
    admin: User = Depends(has_permission("edit_cases")),
):
    try:
        async with _coach_cases_lock:
            if not os.path.exists(COACH_CASES_FILE):
                return {"status": "error", "message": "No cases found"}

            with open(COACH_CASES_FILE, "r", encoding="utf-8") as handle:
                cases = json.load(handle)

            cases = [case for case in cases if case.get("id") != case_id]

            with open(COACH_CASES_FILE, "w", encoding="utf-8") as handle:
                json.dump(cases, handle, ensure_ascii=False, indent=2)

        return {"status": "success", "message": f"Case {case_id} deleted."}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


async def parse_document_content(file: UploadFile):
    safe_filename = os.path.basename(file.filename or "")
    temp_path = os.path.join(os.path.dirname(UPLOAD_DOCS_DIR), f"temp_{uuid.uuid4().hex}_{safe_filename}")
    content = await file.read()

    async with aiofiles.open(temp_path, "wb") as buffer:
        await buffer.write(content)

    try:
        return await parse_document(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
