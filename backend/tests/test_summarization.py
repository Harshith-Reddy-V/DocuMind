"""
Tests for summarization (hierarchical map-reduce) and paper analysis.
"""
from app.services import summarization_service, ingestion_service


def test_summarization_hierarchical(tmp_path, make_pdf):
    pdf_path = str(tmp_path / "long_paper.pdf")
    # Multi-page content
    make_pdf(pdf_path, [
        "Section 1: Introduction to neural document retrieval. Academic assistants must be grounded.",
        "Section 2: Methodology using convolutional neural networks and ChromaDB cosine embeddings.",
        "Section 3: Results demonstrate zero hallucination on out-of-document test queries."
    ])

    doc = ingestion_service.ingest_pdf(pdf_path, "long_paper.pdf")
    doc_id = doc["document_id"]

    summary = summarization_service.summarize_hierarchical(doc["full_text"])
    assert "short_summary" in summary
    assert "detailed_summary" in summary
    assert len(summary["short_summary"]) > 0
    assert len(summary["detailed_summary"]) > 0


def test_paper_analysis_endpoint(client, make_pdf, tmp_path):
    pdf_path = str(tmp_path / "analysis_paper.pdf")
    make_pdf(pdf_path, ["DocuMind research paper content."])

    doc = ingestion_service.ingest_pdf(pdf_path, "analysis_paper.pdf")
    doc_id = doc["document_id"]

    res = client.post(f"/api/documents/{doc_id}/analysis")
    assert res.status_code == 200
    data = res.json()
    assert "title" in data
    assert "authors" in data
    assert "methodology" in data
    assert "results" in data
    assert "limitations" in data


def test_study_guide_endpoint(client, make_pdf, tmp_path):
    pdf_path = str(tmp_path / "study_paper.pdf")
    make_pdf(pdf_path, ["Study guide content."])

    doc = ingestion_service.ingest_pdf(pdf_path, "study_paper.pdf")
    doc_id = doc["document_id"]

    res = client.post(f"/api/documents/{doc_id}/study")
    assert res.status_code == 200
    data = res.json()
    assert "mcqs" in data
    assert "viva_questions" in data
    assert "flashcards" in data
    assert "key_notes" in data
    assert len(data["mcqs"]) > 0
