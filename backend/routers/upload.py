from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
from services.doc_parser import parse_document, chunk_text
from services.rag_service import add_documents_to_db, delete_documents_by_source
from services.llm_client import get_embedding
from services.quote_service import parse_quote_file, load_all_quotes, DATA_DIR as QUOTE_DIR
import uuid

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "docs")
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
