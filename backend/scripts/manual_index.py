import asyncio
import os
import sys
import uuid

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.llm_client import get_embedding
from services.rag_service import add_documents_to_db, delete_documents_by_source

async def manual_index():
    filename = "仲易达集团重大投资信息补充.txt"
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "docs", filename)
    
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Simple chunking by paragraph for this short doc
    chunks = [text.strip()]
    
    print(f"Indexing {filename}...")
    
    # Delete old versions
    delete_documents_by_source(filename)
    
    for i, chunk in enumerate(chunks):
        embedding = await get_embedding(chunk)
        doc_id = f"{filename}_manual_{uuid.uuid4().hex[:8]}"
        add_documents_to_db(
            ids=[doc_id],
            texts=[chunk],
            embeddings=[embedding],
            metadatas=[{"source": filename}]
        )
        print(f"Added chunk {i+1}")

    print("Done!")

if __name__ == "__main__":
    asyncio.run(manual_index())
