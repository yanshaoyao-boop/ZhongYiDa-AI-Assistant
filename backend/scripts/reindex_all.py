import asyncio
import os
import sys
import uuid

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.llm_client import get_embedding
from services.rag_service import add_documents_to_db, collection
from services.doc_parser import parse_document, chunk_text

async def reindex_all():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    docs_dir = os.path.join(data_dir, "docs")
    
    files = [f for f in os.listdir(docs_dir) if os.path.isfile(os.path.join(docs_dir, f))]
    print(f"Found {len(files)} files to index.", flush=True)
    
    success_count = 0
    fail_count = 0

    for filename in files:
        filepath = os.path.join(docs_dir, filename)
        print(f"Indexing {filename}...", flush=True)
        try:
            text = await parse_document(filepath)
            if not text.strip():
                print(f"Skipping empty: {filename}", flush=True)
                continue
            
            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                embedding = await get_embedding(chunk)
                doc_id = f"{filename}_chunk_{i}_{uuid.uuid4().hex[:8]}"
                add_documents_to_db(
                    ids=[doc_id],
                    texts=[chunk],
                    embeddings=[embedding],
                    metadatas=[{"source": filename}]
                )
            print(f"Success: {filename} ({len(chunks)} chunks)", flush=True)
            success_count += 1
        except Exception as e:
            print(f"Error indexing {filename}: {e}", flush=True)
            fail_count += 1

    print(f"Re-indexing complete! Success: {success_count}, Failed: {fail_count}", flush=True)

if __name__ == "__main__":
    asyncio.run(reindex_all())
