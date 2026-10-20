"""
Automated unit and integration tests for the Patent Feasibility Analyzer.
Tests offline with MockGeminiProvider without requiring real Gemini API keys.
"""
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.main import app
from app.services import gemini_service, document_store, vectorstore_service
from app.services.patent_service import INSUFFICIENT_EVIDENCE_APPROACH, _normalize_paper_comparison
from app.models.schemas import PATENT_DISCLAIMER, PaperComparison, FindingEvidence

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_mock_gemini():
    mock_provider = gemini_service.MockGeminiProvider(vector_dim=16)
    gemini_service.set_gemini_provider(mock_provider)
    yield mock_provider
    gemini_service.reset_gemini_provider()


def test_patent_idea_form_validation():
    """Verify that incomplete or invalid idea forms are rejected with 400 or 422."""
    # 1. Missing title
    resp = client.post("/api/patent/analyze", json={
        "title": "",
        "problem_solved": "Slow indexing in distributed databases.",
        "technical_solution": "Use adaptive skip graphs with bloom filters.",
        "idea_description": "A novel data structure for high-speed indexing.",
    })
    assert resp.status_code in [400, 422]

    # 2. Short technical solution
    resp = client.post("/api/patent/analyze", json={
        "title": "Fast Index",
        "problem_solved": "Slow indexing.",
        "technical_solution": "Fast",
        "idea_description": "A novel data structure for high-speed indexing.",
    })
    assert resp.status_code in [400, 422]

    # 3. Missing idea description
    resp = client.post("/api/patent/analyze", json={
        "title": "Fast Index",
        "problem_solved": "Slow indexing in databases.",
        "technical_solution": "Use adaptive skip graphs with bloom filters.",
        "idea_description": "",
    })
    assert resp.status_code in [400, 422]


def test_patent_analysis_potentially_worth_investigation():
    """Verify patent analysis produces grounded comparison and differentiating features."""
    doc_id = "test_doc_novelty_1"
    pages = [
        {"page_number": 1, "text": "This paper presents a baseline convolutional neural network for image classification."},
        {"page_number": 2, "text": "Experimental results demonstrate 85% accuracy on standard benchmarks."}
    ]
    chunks = [
        {"chunk_id": "c1", "page_number": 1, "start_page": 1, "end_page": 1, "text": pages[0]["text"]},
        {"chunk_id": "c2", "page_number": 2, "start_page": 2, "end_page": 2, "text": pages[1]["text"]}
    ]
    embs = gemini_service.embed_batch([c["text"] for c in chunks])
    vectorstore_service.add_chunks(doc_id, chunks, embs)
    document_store.save_document(
        document_id=doc_id,
        filename="baseline_cnn.pdf",
        pages=pages,
        chunks=chunks,
        used_ocr=False
    )

    req_payload = {
        "title": "Quantum-Assisted Neuromorphic Vision Sensor",
        "idea_description": "A novel hybrid quantum-neuromorphic sensor architecture for edge vision processing.",
        "problem_solved": "High energy consumption and latency in conventional CMOS vision processing.",
        "technical_solution": "Integrate superconducting quantum interference devices with asynchronous spike timing circuits.",
        "differentiation_notes": "Eliminates analog-to-digital converter stages completely using direct flux-to-spike modulation.",
        "target_industry": "Autonomous Robotics & Aerospace",
        "jurisdiction": "United States",
        "document_ids": [doc_id]
    }

    resp = client.post("/api/patent/analyze", json=req_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["analysis_id"] is not None
    assert data["title"] == req_payload["title"]
    assert data["preliminary_assessment"] == "Potentially worth further investigation"
    assert len(data["paper_comparisons"]) == 1
    assert data["paper_comparisons"][0]["document_id"] == doc_id
    assert len(data["potentially_differentiating_features"]) > 0
    assert len(data["prior_art_findings"]) > 0
    assert data["prior_art_findings"][0]["page_number"] in [1, 2]
    assert data["disclaimer"] == PATENT_DISCLAIMER
    assert data["external_search_performed"] is False
    assert "novelty" in data["patentability_concerns"]
    assert len(data["suggested_next_steps"]) > 0


def test_patent_analysis_insufficient_evidence():
    """Verify that when no papers or unrelated papers are provided, the system reports insufficient evidence."""
    req_payload = {
        "title": "Insufficient Evidence Test Invention",
        "problem_solved": "Energy dissipation in molecular nanorobotics.",
        "technical_solution": "Self-assembling carbon nanotube rotor assemblies.",
        "differentiation_notes": "Rotational torque generated purely from ambient thermal gradient.",
        "idea_description": "Detailed description of molecular nanorobotics assemblies operating under thermal noise.",
        "document_ids": []  # No papers attached
    }

    resp = client.post("/api/patent/analyze", json=req_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["preliminary_assessment"] == "Insufficient evidence to assess"
    assert "insufficient" in data["preliminary_assessment_explanation"].lower() or "not contain" in data["preliminary_assessment_explanation"].lower()
    assert data["disclaimer"] == PATENT_DISCLAIMER


def test_patent_analysis_significant_overlap():
    """Verify that when the idea duplicates the prior art paper, significant overlap is flagged."""
    doc_id = "test_doc_overlap_1"
    pages = [
        {"page_number": 1, "text": "The proposed system uses a CNN model for visual feature extraction across edge devices."}
    ]
    chunks = [
        {"chunk_id": "ov1", "page_number": 1, "start_page": 1, "end_page": 1, "text": pages[0]["text"]}
    ]
    embs = gemini_service.embed_batch([c["text"] for c in chunks])
    vectorstore_service.add_chunks(doc_id, chunks, embs)
    document_store.save_document(
        document_id=doc_id,
        filename="edge_cnn.pdf",
        pages=pages,
        chunks=chunks,
        used_ocr=False
    )

    req_payload = {
        "title": "Significant Overlap CNN Model",
        "problem_solved": "Visual feature extraction on edge devices.",
        "technical_solution": "The proposed system uses a CNN model for visual feature extraction.",
        "differentiation_notes": "None, identical implementation.",
        "idea_description": "We replicate visual feature extraction with CNN models.",
        "document_ids": [doc_id]
    }

    resp = client.post("/api/patent/analyze", json=req_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["preliminary_assessment"] == "Significant overlap found in supplied papers"
    assert len(data["paper_comparisons"]) == 1
    assert len(data["paper_comparisons"][0]["overlapping_features"]) > 0
    assert data["disclaimer"] == PATENT_DISCLAIMER


def test_patent_persistence_lifecycle():
    """Verify creating, listing, viewing, and deleting saved patent analyses."""
    req_payload = {
        "title": "Saved Analysis Test Invention",
        "problem_solved": "Battery degradation in cold climates.",
        "technical_solution": "Phase-change material heat jackets with micro-thermoelectric heating elements.",
        "differentiation_notes": "Passively retains 80% latent heat during sub-zero idle periods.",
        "idea_description": "A thermal protection system for electric vehicle batteries in arctic conditions.",
        "jurisdiction": "India",
        "document_ids": []
    }

    # 1. Create analysis
    create_resp = client.post("/api/patent/analyze", json=req_payload)
    assert create_resp.status_code == 200
    created_data = create_resp.json()
    analysis_id = created_data["analysis_id"]
    assert analysis_id is not None

    # 2. List saved analyses
    list_resp = client.get("/api/patent/analyses")
    assert list_resp.status_code == 200
    saved_list = list_resp.json()
    found = any(item["analysis_id"] == analysis_id for item in saved_list)
    assert found is True

    # 3. Retrieve specific saved analysis
    get_resp = client.get(f"/api/patent/analyses/{analysis_id}")
    assert get_resp.status_code == 200
    fetched_data = get_resp.json()
    assert fetched_data["analysis_id"] == analysis_id
    assert fetched_data["title"] == req_payload["title"]
    assert fetched_data["jurisdiction"] == "India"
    assert fetched_data["disclaimer"] == PATENT_DISCLAIMER

    # 4. Delete saved analysis
    del_resp = client.delete(f"/api/patent/analyses/{analysis_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    # 5. Verify deletion
    get_again = client.get(f"/api/patent/analyses/{analysis_id}")
    assert get_again.status_code == 404


def test_complete_valid_paper_comparison():
    """Verify that a complete, valid PaperComparison instantiates properly and enforces required fields."""
    valid_data = {
        "document_id": "doc_101",
        "paper_title": "Attention Is All You Need",
        "relevant_approach": "Transformer architecture based entirely on self-attention mechanisms.",
        "overlapping_features": ["Self-attention layers", "Positional encoding"],
        "differences": ["Does not use recurrent or convolutional layers"],
        "strongest_evidence": "The Transformer is the first transduction model relying entirely on self-attention.",
        "page_references": [1, 2],
        "remaining_uncertainties": "Hardware memory scaling for ultra-long sequences.",
    }
    comp = PaperComparison(**valid_data)
    assert comp.document_id == "doc_101"
    assert comp.paper_title == "Attention Is All You Need"
    assert comp.relevant_approach == "Transformer architecture based entirely on self-attention mechanisms."
    assert len(comp.overlapping_features) == 2

    # Verify that omitting relevant_approach directly raises ValidationError
    invalid_data = {
        "document_id": "doc_101",
        "paper_title": "Attention Is All You Need",
        # missing relevant_approach
    }
    with pytest.raises(ValidationError) as exc_info:
        PaperComparison(**invalid_data)
    assert "relevant_approach" in str(exc_info.value)


def test_regression_missing_relevant_approach_healed_from_source_evidence(setup_mock_gemini):
    """
    Regression test: When the LLM response omits 'relevant_approach', the service
    heals the field using retrieved factual source evidence rather than failing validation.
    """
    doc_id = "test_doc_missing_approach_1"
    pages = [
        {"page_number": 1, "text": "This research details a multi-agent reinforcement learning controller for microgrids."}
    ]
    chunks = [
        {"chunk_id": "c_ma_1", "page_number": 1, "start_page": 1, "end_page": 1, "text": pages[0]["text"]}
    ]
    embs = gemini_service.embed_batch([c["text"] for c in chunks])
    vectorstore_service.add_chunks(doc_id, chunks, embs)
    document_store.save_document(
        document_id=doc_id,
        filename="microgrid_marl.pdf",
        pages=pages,
        chunks=chunks,
        used_ocr=False
    )

    # Force mock provider to omit relevant_approach from each comparison
    setup_mock_gemini.force_missing_approach = True

    req_payload = {
        "title": "Decentralized Microgrid Controller",
        "idea_description": "A decentralized peer-to-peer energy dispatch controller using multi-agent consensus algorithms.",
        "problem_solved": "Single points of failure in centralized power grid dispatch systems.",
        "technical_solution": "Deploy localized edge nodes executing asynchronous consensus and multi-agent control.",
        "differentiation_notes": "Cryptographically signed energy token bidding protocol.",
        "target_industry": "Energy and Utilities",
        "jurisdiction": "United States",
        "document_ids": [doc_id]
    }

    resp = client.post("/api/patent/analyze", json=req_payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert data["analysis_id"] is not None
    assert len(data["paper_comparisons"]) == 1
    comp = data["paper_comparisons"][0]
    assert comp["document_id"] == doc_id
    assert comp["paper_title"] == "microgrid_marl.pdf"
    # Verify relevant_approach was constructed factually from the source chunk
    assert "relevant_approach" in comp
    assert len(comp["relevant_approach"]) > 0
    assert "Disclosed approach in excerpt" in comp["relevant_approach"]
    assert "multi-agent reinforcement learning controller" in comp["relevant_approach"]


def test_regression_missing_approach_insufficient_evidence_case():
    """
    Verify that when relevant_approach is missing and the paper has no excerpts/chunks,
    the neutral INSUFFICIENT_EVIDENCE_APPROACH phrase is assigned.
    """
    raw_pc = {
        "document_id": "doc_empty_1",
        "paper_title": "empty_paper.pdf",
        # missing relevant_approach
    }
    evidence_list = [{
        "document_id": "doc_empty_1",
        "paper_title": "empty_paper.pdf",
        "chunks": [],  # No chunks available
    }]

    normalized = _normalize_paper_comparison(raw_pc, evidence_list, 0)
    assert isinstance(normalized, PaperComparison)
    assert normalized.document_id == "doc_empty_1"
    assert normalized.paper_title == "empty_paper.pdf"
    assert normalized.relevant_approach == INSUFFICIENT_EVIDENCE_APPROACH


def test_regression_malformed_gemini_response_handling(setup_mock_gemini):
    """
    Regression test: When the LLM returns a malformed response (non-list paper_comparisons,
    missing sections), the service recovers safely, returns 200 with a valid report,
    and constructs valid PaperComparison entries for the supplied documents.
    """
    doc_id = "test_doc_malformed_1"
    pages = [
        {"page_number": 1, "text": "A framework for zero-knowledge succinct non-interactive arguments of knowledge (zk-SNARKs)."}
    ]
    chunks = [
        {"chunk_id": "c_zk_1", "page_number": 1, "start_page": 1, "end_page": 1, "text": pages[0]["text"]}
    ]
    embs = gemini_service.embed_batch([c["text"] for c in chunks])
    vectorstore_service.add_chunks(doc_id, chunks, embs)
    document_store.save_document(
        document_id=doc_id,
        filename="zk_snarks_foundation.pdf",
        pages=pages,
        chunks=chunks,
        used_ocr=False
    )

    setup_mock_gemini.force_malformed_response = True

    req_payload = {
        "title": "Recursive ZK-Rollup Pipeline",
        "idea_description": "High-throughput blockchain scaling using recursive zk-SNARK verification circuits.",
        "problem_solved": "Layer-1 gas limits and verification latency in decentralized ledgers.",
        "technical_solution": "Batch 10,000 transactions into recursive proof trees verified in constant time.",
        "differentiation_notes": "Halo-style accumulation schemes with customized lookup tables.",
        "target_industry": "FinTech / Cryptography",
        "jurisdiction": "United States",
        "document_ids": [doc_id]
    }

    resp = client.post("/api/patent/analyze", json=req_payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert data["analysis_id"] is not None
    assert data["title"] == req_payload["title"]
    assert isinstance(data["paper_comparisons"], list)
    assert len(data["paper_comparisons"]) == 1
    comp = data["paper_comparisons"][0]
    assert comp["document_id"] == doc_id
    assert comp["paper_title"] == "zk_snarks_foundation.pdf"
    assert "relevant_approach" in comp
    assert len(comp["relevant_approach"]) > 0
    # Must be validly retrievable from persistence
    get_resp = client.get(f"/api/patent/analyses/{data['analysis_id']}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["analysis_id"] == data["analysis_id"]
    assert len(retrieved["paper_comparisons"]) == 1

