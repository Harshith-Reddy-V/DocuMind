"""
Tests for persistence: verifying SQLite metadata and ChromaDB vectors survive server restart.
"""
from app.services import ingestion_service, document_store, vectorstore_service, rag_service


def test_scenario_f_persistence_across_restart(tmp_path, make_pdf, setup_test_environment):
    """
    Scenario F: Ingest a document, simulate backend restart, and verify metadata & vectors remain usable.
    """
    pdf_path = str(tmp_path / "persistent_paper.pdf")
    make_pdf(pdf_path, [
        "Persistence Test: The proposed system uses a CNN model for robust text classification."
    ])

    # 1. Ingest document
    doc = ingestion_service.ingest_pdf(pdf_path, "persistent_paper.pdf")
    doc_id = doc["document_id"]
    assert doc["status"] == "ready"
    assert doc["num_pages"] == 1
    assert doc["num_chunks"] > 0

    # 2. Simulate Backend Restart
    # Clear client caches and connections
    vectorstore_service._client = None

    # 3. Verify Document Metadata in SQLite
    reloaded_doc = document_store.get_document(doc_id)
    assert reloaded_doc is not None
    assert reloaded_doc["document_id"] == doc_id
    assert reloaded_doc["filename"] == "persistent_paper.pdf"
    assert reloaded_doc["status"] == "ready"
    assert reloaded_doc["num_pages"] == 1
    assert reloaded_doc["num_chunks"] == doc["num_chunks"]

    # 4. Verify Vector Store Querying
    answer = rag_service.answer_question(doc_id, "What model does the system use?", threshold=0.0)
    assert answer["grounded"] is True
    assert "CNN model" in answer["answer"]
    assert len(answer["sources"]) > 0
    assert answer["sources"][0]["page"] == 1
