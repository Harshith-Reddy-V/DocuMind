"""
Tests for vectorstore_service: Cosine metric configuration, similarity calculations, and storage.
"""
from app.services import vectorstore_service


def test_cosine_metric_and_similarity_scoring():
    """Scenario G: Test mathematical consistency of cosine space and score conversion."""
    document_id = "test_cosine_doc"
    # Create chunks
    chunks = [
        {"chunk_id": "c1", "text": "Identical chunk", "page_number": 1, "start_page": 1, "end_page": 1},
        {"chunk_id": "c2", "text": "Orthogonal chunk", "page_number": 2, "start_page": 2, "end_page": 2},
    ]
    # Unit vectors: c1 is [1.0, 0.0], c2 is [0.0, 1.0]
    embeddings = [
        [1.0, 0.0],
        [0.0, 1.0],
    ]
    vectorstore_service.add_chunks(document_id, chunks, embeddings)

    # Query with [1.0, 0.0]
    results = vectorstore_service.query(document_id, query_embedding=[1.0, 0.0], top_k=2)

    assert len(results) == 2
    # First result should be c1 (identical vector)
    assert results[0]["chunk_id"] == "c1"
    # Cosine distance = 0.0 -> similarity = 1.0 - 0.0 = 1.0
    assert abs(results[0]["distance"] - 0.0) < 1e-4
    assert abs(results[0]["score"] - 1.0) < 1e-4

    # Second result should be c2 (orthogonal vector)
    assert results[1]["chunk_id"] == "c2"
    # Cosine distance = 1.0 -> similarity = 1.0 - 1.0 = 0.0
    assert abs(results[1]["distance"] - 1.0) < 1e-4
    assert abs(results[1]["score"] - 0.0) < 1e-4

    # Cleanup
    assert vectorstore_service.delete_document(document_id) is True
