
import os
import sys
import asyncio

# Add the parent directory to sys.path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.doc_parser import parse_document, chunk_text
from services.rag_service import add_documents_to_db, delete_documents_by_source
from services.llm_client import get_embedding

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "docs")

async def reindex_all():
    if not os.path.exists(DOCS_DIR):
        print(f"Directory {DOCS_DIR} does not exist.")
        return

    files = [f for f in os.listdir(DOCS_DIR) if os.path.isfile(os.path.join(DOCS_DIR, f))]
    only_file = os.getenv("ONLY_FILE")
    if only_file:
        files = [f for f in files if f == only_file]
        print(f"Filtering to only process: {only_file}")
    else:
        # Sort files to process smaller/faster ones first
        files.sort(key=lambda x: os.path.getsize(os.path.join(DOCS_DIR, x)))

    print(f"Found {len(files)} files to process in {DOCS_DIR}")

    for filename in files:
        file_path = os.path.join(DOCS_DIR, filename)
        print(f"Processing {filename}...")
        
        try:
            # 1. Parse document
            text = await parse_document(file_path)
            if not text.strip():
                print(f"Skipping {filename}: No text extracted.")
                continue
            
            # 2. Chunk text
            chunks = chunk_text(text)
            print(f"Created {len(chunks)} chunks for {filename}")
            
            # 3. Get embeddings
            embeddings = []
            for i, chunk in enumerate(chunks):
                print(f"  Embedding chunk {i+1}/{len(chunks)}...")
                emb = await get_embedding(chunk)
                embeddings.append(emb)
            
            # 4. Clear old and add to DB
            delete_documents_by_source(filename)
            
            ids = [f"{filename}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": filename} for _ in range(len(chunks))]
            
            add_documents_to_db(ids, chunks, embeddings, metadatas)
            print(f"Successfully indexed {filename}")
            
        except Exception as e:
            print(f"Error indexing {filename}: {e}")

if __name__ == "__main__":
    asyncio.run(reindex_all())
