from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from services.doc_parser import parse_document, chunk_text
from services.rag_service import add_documents_to_db, delete_documents_by_source
from services.llm_client import get_embedding, analyze_coach_case
from services.quote_service import parse_quote_file, load_all_quotes, DATA_DIR as QUOTE_DIR
import uuid
import json
import asyncio
import aiofiles

# 全局文件锁，防止并发请求同时覆盖 coach_cases.json
_coach_cases_lock = asyncio.Lock()

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "docs")
COACH_CASES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "coach_cases.json")
os.makedirs(UPLOAD_DOCS_DIR, exist_ok=True)
os.makedirs(QUOTE_DIR, exist_ok=True)

@router.post("/document")
async def upload_document(file: UploadFile = File(...), category: str = "biz"):
    """Upload and process a knowledge base document (Word/PDF/TXT), with category."""
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(UPLOAD_DOCS_DIR, safe_filename)
    # 使用异步 I/O 写入，防止阻塞事件循环
    content = await file.read()
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(content)
        
    try:
        # 解捸文档
        text = await parse_document(file_path)
        if not text.strip():
            return {"status": "error", "message": "No text could be extracted from the document."}
            
        # 分块文本
        chunks = chunk_text(text)
        
        # 统一使用 safe_filename 作为向量库的唯一键（相比原始 file.filename 可能带路径）
        source_name = safe_filename
        
        # 删除旧片段，防止重复入库
        await asyncio.to_thread(delete_documents_by_source, source_name)
        
        # 获取 embedding 并保存到 ChromaDB
        for i, chunk in enumerate(chunks):
            embedding = await get_embedding(chunk)
            doc_id = f"{safe_filename}_chunk_{i}_{uuid.uuid4().hex[:8]}"
            await asyncio.to_thread(
                add_documents_to_db,
                ids=[doc_id],
                texts=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": safe_filename, "category": category}]
            )
            
        return {"status": "success", "message": f"Document {safe_filename} processed successfully. Extracted {len(chunks)} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quote")
async def upload_quote(file: UploadFile = File(...)):
    """Upload and process a quote spreadsheet (Excel/CSV)."""
    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(QUOTE_DIR, safe_filename)
    # 异步写入
    content = await file.read()
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(content)
        
    try:
        # Validate format parseable
        data_list = await asyncio.to_thread(parse_quote_file, file_path)
        if not data_list:
            return {"status": "error", "message": "Failed to parse spreadsheet or file is empty."}
            
        # Reload cache
        await asyncio.to_thread(load_all_quotes)
        return {"status": "success", "message": f"Quote file {safe_filename} uploaded and parsed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents(category: str = None):
    """List all uploaded knowledge base documents."""
    try:
        if not os.path.exists(UPLOAD_DOCS_DIR):
            return {"files": []}
        
        # We need to query chromadb or just list files. 
        # Since files are mixed in the directory, returning all is fine if we don't have a DB tracker, 
        # but to filter by category we must query ChromaDB to see what files belong to what category.
        import chromadb
        from services.rag_service import collection
        
        if category:
            # Get distinct sources for this category
            results = collection.get(where={"category": category}, include=["metadatas"])
            files = list(set([m["source"] for m in results["metadatas"]]))
        else:
            files = [f for f in os.listdir(UPLOAD_DOCS_DIR) if os.path.isfile(os.path.join(UPLOAD_DOCS_DIR, f))]
        
        # Sort by modification time, newest first (if file exists locally)
        files = [f for f in files if os.path.exists(os.path.join(UPLOAD_DOCS_DIR, f))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOAD_DOCS_DIR, x)), reverse=True)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/document/{filename}")
async def delete_document(filename: str):
    """Delete a document and its knowledge base chunks."""
    try:
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(UPLOAD_DOCS_DIR, safe_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Delete from ChromaDB
        await asyncio.to_thread(delete_documents_by_source, filename)
        return {"status": "success", "message": f"Document {filename} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quotes")
async def list_quotes():
    """List all uploaded quote files."""
    try:
        if not os.path.exists(QUOTE_DIR):
            return {"files": []}
        files = [f for f in os.listdir(QUOTE_DIR) if os.path.isfile(os.path.join(QUOTE_DIR, f))]
        # Sort by modification time, newest first
        files.sort(key=lambda x: os.path.getmtime(os.path.join(QUOTE_DIR, x)), reverse=True)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/quote/{filename}")
async def delete_quote(filename: str):
    """Delete a quote file from the system."""
    try:
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(QUOTE_DIR, safe_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Reload cache to reflect deletion
        load_all_quotes()
        return {"status": "success", "message": f"Quote file {filename} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/coach-case")
async def create_coach_case(file: UploadFile = File(...)):
    """Upload raw records, split multiple cases if exists, wash them with LLM, and save."""
    try:
        content = await parse_document_content(file)
        print(f">> Received file: {file.filename}, length: {len(content)}")
        
        # 更加健壮的拆分逻辑
        import re
        # 匹配 "案例 X：" 或 "案例X:" 或 "案例X"
        case_blocks = re.split(r'(?=案例\s*\d+\s*[:：]|\={5,})', content)
        
        # 过滤并清洗块内容
        case_texts = []
        for block in case_blocks:
            cleaned = block.strip()
            # 移除分隔符行
            cleaned = re.sub(r'\={5,}', '', cleaned).strip()
            if len(cleaned) > 20: # 稍微长一点才算有效案例
                case_texts.append(cleaned)
        
        print(f">> Found {len(case_texts)} potential cases in file.")
        
        new_cases = []
        # 限制单次批次处理数量，防止 HTTP 超时 (增加到30，满足用户一次传20的需求)
        batch_limit = 30 
        for i, text in enumerate(case_texts[:batch_limit]):
            try:
                print(f">> Processing case {i+1}/{min(len(case_texts), batch_limit)}...")
                # 深度清洗剧本，增加 filename 作为引导
                case_data = await analyze_coach_case(text, hint=file.filename)
                print(f">> Successfully analyzed case: {case_data.get('name')}")
                case_data["id"] = uuid.uuid4().hex[:8]
                case_data["source"] = file.filename
                new_cases.append(case_data)
            except Exception as e:
                print(f"!! Error processing case block {i}: {e}")
                continue
        
        # 加锁，防止并发请求丢失数据
        async with _coach_cases_lock:
            # 加载现有剧本
            cases = []
            if os.path.exists(COACH_CASES_FILE):
                with open(COACH_CASES_FILE, "r", encoding="utf-8") as f:
                    cases = json.load(f)
            
            # 合并 (新生成的排在前面)
            combined = new_cases + cases
            with open(COACH_CASES_FILE, "w", encoding="utf-8") as f:
                json.dump(combined, f, ensure_ascii=False, indent=2)
            
        print(f">> Successfully processed {len(new_cases)} cases.")
        return {
            "status": "success", 
            "processed_count": len(new_cases),
            "total_found": len(case_texts),
            "note": "为了保证分析质量，系统单次批量处理前10条。如有更多，请分批上传或联系管理员。" if len(case_texts) > batch_limit else ""
        }
    except Exception as e:
        print(f"!! Global error in create_coach_case: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/coach-cases")
async def list_coach_cases(category: str = None):
    """List structured coach cases, optionally filtered by category."""
    try:
        if not os.path.exists(COACH_CASES_FILE):
            return []
        with open(COACH_CASES_FILE, "r", encoding="utf-8") as f:
            cases = json.load(f)
        
        if category:
            return [c for c in cases if category in c.get('category', '')]
        return cases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/coach-case/{case_id}")
async def delete_coach_case(case_id: str):
    """Delete a specific coach case."""
    try:
        async with _coach_cases_lock:
            if not os.path.exists(COACH_CASES_FILE):
                return {"status": "error", "message": "No cases found"}
                
            with open(COACH_CASES_FILE, "r", encoding="utf-8") as f:
                cases = json.load(f)
                
            cases = [c for c in cases if c.get("id") != case_id]
            
            with open(COACH_CASES_FILE, "w", encoding="utf-8") as f:
                json.dump(cases, f, ensure_ascii=False, indent=2)
                
        return {"status": "success", "message": f"Case {case_id} deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def parse_document_content(file: UploadFile):
    """Temporary helper to get text content from upload."""
    safe_filename = os.path.basename(file.filename)
    temp_path = os.path.join(os.path.dirname(UPLOAD_DOCS_DIR), f"temp_{uuid.uuid4().hex}_{safe_filename}")
    # 异步写入临时文件
    content = await file.read()
    async with aiofiles.open(temp_path, "wb") as buffer:
        await buffer.write(content)
    try:
        text = await parse_document(temp_path)
        return text
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
