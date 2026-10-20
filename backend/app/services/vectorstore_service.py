"""
ChromaDB persistent vector store service.

Convention & Distance Semantics:
- Collections are explicitly created with `metadata={"hnsw:space": "cosine"}`.
- In ChromaDB with cosine space, the reported distance is cosine distance:
      distance = 1 - cosine_similarity
- Therefore, the true cosine similarity is calculated as:
      cosine_similarity = 1 - distance
- Cosine similarity ranges from -1.0 to 1.0 (with 1.0 being identical and 0.0 being orthogonal).
- Variables are strictly named `distance` and `similarity` (never conflated).
"""
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[chromadb.PersistentClient] = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        settings.ensure_directories()
        _client = chromadb.PersistentClient(
            path=settings.VECTOR_DB_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def _collection_name(document_id: str) -> str:
    # Chroma collection names must be 3-63 chars, alphanum, underscores, hyphens
    sanitized = document_id.replace("-", "_")
    return f"doc_{sanitized}"


def collection_exists(document_id: str) -> bool:
    """Check if collection exists for given document ID."""
    client = get_chroma_client()
    try:
        client.get_collection(name=_collection_name(document_id))
        return True
    except Exception:
        return False


def get_or_create_collection(document_id: str):
    """Retrieve or initialize Chroma collection explicitly configured with cosine metric."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=_collection_name(document_id),
        metadata={"hnsw:space": "cosine"}
    )


def add_chunks(document_id: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]], batch_size: int = 250):
    """
    Store chunk texts, embeddings, and page metadata into ChromaDB.
    chunks: list of dicts with keys: chunk_id, text, start_page, end_page (or page_number)
    embeddings: list of float vectors matching chunks
    """
    if not chunks:
        return

    if len(chunks) != len(embeddings):
        raise ValueError(f"Mismatch between number of chunks ({len(chunks)}) and embeddings ({len(embeddings)})")

    collection = get_or_create_collection(document_id)

    # Batch insertions to respect limits
    total = len(chunks)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch_chunks = chunks[start:end]
        batch_embeddings = embeddings[start:end]

        ids = [c["chunk_id"] for c in batch_chunks]
        documents = [c["text"] for c in batch_chunks]
        metadatas = []
        for c in batch_chunks:
            meta = {
                "chunk_id": c["chunk_id"],
                "document_id": document_id,
                "start_page": int(c.get("start_page", c.get("page_number", 1))),
                "end_page": int(c.get("end_page", c.get("page_number", 1))),
                "page_number": int(c.get("page_number", c.get("start_page", 1))),
            }
            metadatas.append(meta)

        collection.add(
            ids=ids,
            embeddings=batch_embeddings,
            documents=documents,
            metadatas=metadatas,
        )
    logger.info(f"Added {total} chunks to collection {_collection_name(document_id)}")


def query(document_id: str, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search against the document collection.
    Returns: list of dicts with chunk_id, page_number, start_page, end_page, text, distance, score (similarity).
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(name=_collection_name(document_id))
    except Exception:
        logger.warning(f"Collection for document {document_id} not found.")
        return []

    count = collection.count()
    if count == 0:
        return []

    actual_k = min(top_k, count)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=actual_k,
        include=["documents", "metadatas", "distances"]
    )

    output = []
    if not results or not results.get("ids") or not results["ids"][0]:
        return output

    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for i in range(len(ids)):
        raw_distance = float(distances[i])
        # Since collection uses cosine space: cosine_similarity = 1.0 - cosine_distance
        cosine_similarity = 1.0 - raw_distance

        meta = metas[i] if metas and i < len(metas) else {}
        output.append({
            "chunk_id": ids[i],
            "page_number": meta.get("page_number", meta.get("start_page", 1)),
            "start_page": meta.get("start_page", meta.get("page_number", 1)),
            "end_page": meta.get("end_page", meta.get("page_number", 1)),
            "text": docs[i],
            "distance": round(raw_distance, 4),
            "score": round(float(cosine_similarity), 4),
        })

    return output


def delete_document(document_id: str) -> bool:
    """Delete Chroma collection for given document."""
    client = get_chroma_client()
    try:
        client.delete_collection(name=_collection_name(document_id))
        return True
    except Exception as e:
        logger.warning(f"Could not delete collection for document {document_id}: {e}")
        return False
