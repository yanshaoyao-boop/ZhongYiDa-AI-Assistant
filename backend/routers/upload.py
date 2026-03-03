from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from services.doc_parser import parse_document, chunk_text
from services.rag_service import add_documents_to_db, delete_documents_by_source
from services.llm_client import get_embedding, analyze_coach_case
from services.quote_service import parse_quote_file, load_all_quotes, DATA_DIR as QUOTE_DIR
import uuid
import json

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "docs")
COACH_CASES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "coach_cases.json")
os.makedirs(UPLOAD_DOCS_DIR, exist_ok=True)
os.makedirs(QUOTE_DIR, exist_ok=True)

@router.post("/document")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a knowledge base document (Word/PDF/TXT)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    file_path = os.path.join(UPLOAD_DOCS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Parse document
        text = await parse_document(file_path)
        if not text.strip():
            return {"status": "error", "message": "No text could be extracted from the document."}
            
        # Chunk text
        chunks = chunk_text(text)
        
        # Determine unique source name
        source_name = file.filename
        
        # DELETE old overlapping chunks if they exist to prevent memory duplication and conflict
        delete_documents_by_source(source_name)
        
        # Get embeddings and save to ChromaDB
        for i, chunk in enumerate(chunks):
            embedding = await get_embedding(chunk)
            doc_id = f"{file.filename}_chunk_{i}_{uuid.uuid4().hex[:8]}"
            add_documents_to_db(
                ids=[doc_id],
                texts=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": file.filename}]
            )
            
        return {"status": "success", "message": f"Document {file.filename} processed successfully. Extracted {len(chunks)} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quote")
async def upload_quote(file: UploadFile = File(...)):
    """Upload and process a quote spreadsheet (Excel/CSV)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    file_path = os.path.join(QUOTE_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Validate format parseable
        df = parse_quote_file(file_path)
        if df.empty:
            return {"status": "error", "message": "Failed to parse spreadsheet or file is empty."}
            
        # Reload cache
        load_all_quotes()
        return {"status": "success", "message": f"Quote file {file.filename} uploaded and parsed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents():
    """List all uploaded knowledge base documents."""
    try:
        if not os.path.exists(UPLOAD_DOCS_DIR):
            return {"files": []}
        files = [f for f in os.listdir(UPLOAD_DOCS_DIR) if os.path.isfile(os.path.join(UPLOAD_DOCS_DIR, f))]
        # Sort by modification time, newest first
        files.sort(key=lambda x: os.path.getmtime(os.path.join(UPLOAD_DOCS_DIR, x)), reverse=True)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/document/{filename}")
async def delete_document(filename: str):
    """Delete a document and its knowledge base chunks."""
    try:
        file_path = os.path.join(UPLOAD_DOCS_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Delete from ChromaDB
        delete_documents_by_source(filename)
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
        file_path = os.path.join(QUOTE_DIR, filename)
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
        # 限制单次批次处理数量，防止 HTTP 超时 (豆包分析一个案例约需 3-7s)
        batch_limit = 10 
        for i, text in enumerate(case_texts[:batch_limit]):
            try:
                print(f">> Processing case {i+1}/{min(len(case_texts), batch_limit)}...")
                # 深度清洗剧本
                case_data = await analyze_coach_case(text)
                case_data["id"] = uuid.uuid4().hex[:8]
                case_data["source"] = file.filename
                new_cases.append(case_data)
            except Exception as e:
                print(f"!! Error processing case block {i}: {e}")
                continue
        
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
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        text = await parse_document(temp_path)
        return text
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
