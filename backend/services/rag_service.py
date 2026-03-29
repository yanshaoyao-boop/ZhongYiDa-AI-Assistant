import chromadb
import os

# Define where to persist the data locally
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=os.path.join(DATA_DIR, "chromadb"))
COLLECTION_NAME = "zhongyida_kb"

def get_collection():
    """Get or create the knowledge base collection"""
    # Create a vector collection, distance function defaults to l2, we can use cosine
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
collection = get_collection()


def _has_query_hits(results: dict | None) -> bool:
    if not results:
        return False
    ids = results.get("ids") or []
    return bool(ids and ids[0])


def _format_query_results(results: dict | None) -> list[dict]:
    formatted_results = []
    if not _has_query_hits(results):
        return formatted_results

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for i in range(len(ids)):
        formatted_results.append(
            {
                "id": ids[i],
                "document": documents[i],
                "metadata": metadatas[i],
                "distance": distances[i],
            }
        )
    return formatted_results


def _is_legacy_untyped_doc(row: dict) -> bool:
    metadata = row.get("metadata") or {}
    return not metadata.get("category")

def add_documents_to_db(ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict]):
    """Store text chunks and their corresponding embeddings to ChromaDB"""
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

def delete_documents_by_source(source_name: str):
    """Delete all chunks belonging to a specific file from ChromaDB"""
    try:
        collection.delete(
            where={"source": source_name}
        )
    except Exception as e:
        print(f"Error deleting previous chunks for {source_name}: {e}")


def delete_legacy_untyped_documents_by_source(source_name: str):
    """Delete legacy chunks for a source whose metadata has no category."""
    try:
        existing = collection.get(where={"source": source_name}, include=["metadatas"])
        ids = existing.get("ids") or []
        metas = existing.get("metadatas") or []
        legacy_ids = []
        for doc_id, metadata in zip(ids, metas):
            category = (metadata or {}).get("category")
            if not category:
                legacy_ids.append(doc_id)
        if legacy_ids:
            collection.delete(ids=legacy_ids)
    except Exception as e:
        print(f"Error deleting legacy untyped chunks for {source_name}: {e}")


def delete_documents_by_source_key(source_key: str):
    """Delete all chunks belonging to a specific categorized source from ChromaDB."""
    try:
        collection.delete(
            where={"source_key": source_key}
        )
    except Exception as e:
        print(f"Error deleting previous chunks for {source_key}: {e}")


def search_similar_documents(query_embedding: list[float], n_results: int = 3, category: str = None):
    """Search for the most similar document chunks given a query embedding"""

    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
    }

    if category:
        query_params["where"] = {"category": category}

    results = collection.query(**query_params)
    formatted = _format_query_results(results)

    if not category:
        return formatted

    # Backward compatibility: historical chunks may miss `category`.
    # If filtered hits are empty OR insufficient, supplement from untyped legacy chunks.
    if len(formatted) < n_results:
        unfiltered_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=max(n_results * 4, n_results),
        )
        unfiltered_rows = _format_query_results(unfiltered_results)
        legacy_rows = [row for row in unfiltered_rows if _is_legacy_untyped_doc(row)]

        seen_ids = {row["id"] for row in formatted}
        for row in legacy_rows:
            if row["id"] in seen_ids:
                continue
            formatted.append(row)
            seen_ids.add(row["id"])
            if len(formatted) >= n_results:
                break

        # If still empty, keep previous behavior: fallback to unfiltered candidates.
        if not formatted:
            return unfiltered_rows[:n_results]

    return formatted
