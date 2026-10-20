"""
Tests for API upload, filename collisions, status polling, and deletion.
"""
import io
import os
import time
from app.config import settings
from app.services import document_store, vectorstore_service


def test_upload_non_pdf_fails(client):
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", b"Hello world", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_upload_empty_pdf_fails(client):
    response = client.post(
        "/api/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_oversized_pdf_fails(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 1)
    huge_data = b"%PDF-" + b"0" * (2 * 1024 * 1024)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("huge.pdf", huge_data, "application/pdf")}
    )
    assert response.status_code == 400
    assert "File too large" in response.json()["detail"]


def test_filename_collision_prevention(client, make_pdf, tmp_path):
    """Bug 5: Two uploads with identical original filenames must not collide or overwrite."""
    pdf1_path = str(tmp_path / "pdf1.pdf")
    pdf2_path = str(tmp_path / "pdf2.pdf")

    make_pdf(pdf1_path, ["First document content."])
    make_pdf(pdf2_path, ["Second document content."])

    with open(pdf1_path, "rb") as f1, open(pdf2_path, "rb") as f2:
        res1 = client.post("/api/documents/upload", files={"file": ("paper.pdf", f1, "application/pdf")})
        res2 = client.post("/api/documents/upload", files={"file": ("paper.pdf", f2, "application/pdf")})

    assert res1.status_code == 200
    assert res2.status_code == 200

    data1 = res1.json()
    data2 = res2.json()

    # Different document IDs
    assert data1["document_id"] != data2["document_id"]
    assert data1["filename"] == "paper.pdf"
    assert data2["filename"] == "paper.pdf"

    # Both records exist in database
    doc1 = document_store.get_document(data1["document_id"])
    doc2 = document_store.get_document(data2["document_id"])
    assert doc1 is not None
    assert doc2 is not None
    assert doc1["storage_path"] != doc2["storage_path"]
    assert os.path.exists(doc1["storage_path"])
    assert os.path.exists(doc2["storage_path"])


def test_document_status_endpoint(client, make_pdf, tmp_path):
    """Bug 8 & 9: Verify status endpoint returns processing stage and progress."""
    pdf_path = str(tmp_path / "status_test.pdf")
    make_pdf(pdf_path, ["Valid content for status polling."])

    with open(pdf_path, "rb") as f:
        res = client.post("/api/documents/upload", files={"file": ("status_test.pdf", f, "application/pdf")})
    assert res.status_code == 200
    doc_id = res.json()["document_id"]

    status_res = client.get(f"/api/documents/{doc_id}/status")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["document_id"] == doc_id
    assert "current_stage" in data
    assert "progress_percent" in data
    assert isinstance(data["warnings"], list)


def test_delete_document_cleans_up_all_resources(client, make_pdf, tmp_path):
    """Bug 13: Delete endpoint removes metadata, file on disk, and ChromaDB collection."""
    pdf_path = str(tmp_path / "del_test.pdf")
    make_pdf(pdf_path, ["Deletable content."])

    with open(pdf_path, "rb") as f:
        res = client.post("/api/documents/upload", files={"file": ("del.pdf", f, "application/pdf")})
    doc_id = res.json()["document_id"]

    # Verify exists
    doc = document_store.get_document(doc_id)
    assert doc is not None
    stored_path = doc["storage_path"]
    assert os.path.exists(stored_path)

    # Delete
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Verify cleaned up
    assert document_store.get_document(doc_id) is None
    assert not os.path.exists(stored_path)
    assert not vectorstore_service.collection_exists(doc_id)
