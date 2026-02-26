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

def add_documents_to_db(ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict]):
    """Store text chunks and their corresponding embeddings to ChromaDB"""
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

def search_similar_documents(query_embedding: list[float], n_results: int = 3):
    """Search for the most similar document chunks given a query embedding"""
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    # Return formatted results
    formatted_results = []
    if results and len(results['ids'][0]) > 0:
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i]
            })
    return formatted_results
