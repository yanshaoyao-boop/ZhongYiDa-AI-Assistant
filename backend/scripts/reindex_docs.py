
import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to sys.path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.doc_parser import parse_document, chunk_text
from services.rag_service import add_documents_to_db, delete_documents_by_source, delete_documents_by_source_key
from services.llm_client import get_embedding

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "docs")
DOCUMENT_CATEGORIES = {"admin", "biz"}


def iter_doc_files(docs_dir: str):
    docs_root = Path(docs_dir)
    for file_path in sorted(docs_root.rglob("*")):
        if not file_path.is_file():
            continue

        relative_path = file_path.relative_to(docs_root)
        category = relative_path.parts[0] if len(relative_path.parts) > 1 and relative_path.parts[0] in DOCUMENT_CATEGORIES else None
        yield file_path, category

async def reindex_all():
    if not os.path.exists(DOCS_DIR):
        print(f"Directory {DOCS_DIR} does not exist.")
        return

    files = list(iter_doc_files(DOCS_DIR))
    only_file = os.getenv("ONLY_FILE")
    if only_file:
        files = [item for item in files if item[0].name == only_file]
        print(f"Filtering to only process: {only_file}")
    else:
        # Sort files to process smaller/faster ones first
        files.sort(key=lambda item: item[0].stat().st_size)

    print(f"Found {len(files)} files to process in {DOCS_DIR}")

    for file_path, category in files:
        filename = file_path.name
        source_key = f"{category or 'root'}::{filename}"
        print(f"Processing {file_path.relative_to(Path(DOCS_DIR))}...")
        
        try:
            # 1. Parse document
            text = await parse_document(str(file_path))
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
            delete_documents_by_source_key(source_key)
            if category is None:
                delete_documents_by_source(filename)
            
            ids = [f"{filename}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "source": filename,
                    "source_key": source_key,
                    **({"category": category} if category else {}),
                }
                for _ in range(len(chunks))
            ]
            
            add_documents_to_db(ids, chunks, embeddings, metadatas)
            print(f"Successfully indexed {filename}")
            
        except Exception as e:
            print(f"Error indexing {filename}: {e}")

if __name__ == "__main__":
    asyncio.run(reindex_all())
