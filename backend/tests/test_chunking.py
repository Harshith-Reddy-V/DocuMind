"""
Tests for chunking service: paragraph and sentence boundaries, overlap, and page attribution.
"""
from app.services import chunking_service
from app.services.pdf_service import PageExtractionResult


def test_chunking_preserves_page_attribution():
    pages = [
        PageExtractionResult(page_number=1, text="First page content. System overview.", used_ocr=False, status="success"),
        PageExtractionResult(page_number=2, text="Second page content. CNN methodology details.", used_ocr=False, status="success"),
    ]
    chunks = chunking_service.chunk_pages(pages, document_id="doc_123", chunk_size=800, chunk_overlap=150)
    assert len(chunks) == 2
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["start_page"] == 1
    assert chunks[0]["end_page"] == 1
    assert "First page" in chunks[0]["text"]

    assert chunks[1]["page_number"] == 2
    assert chunks[1]["start_page"] == 2
    assert chunks[1]["end_page"] == 2
    assert "Second page" in chunks[1]["text"]


def test_chunking_skips_empty_and_failed_pages():
    pages = [
        PageExtractionResult(page_number=1, text="", used_ocr=True, status="failed", warning="OCR failed"),
        PageExtractionResult(page_number=2, text="Valid content here.", used_ocr=False, status="success"),
        PageExtractionResult(page_number=3, text="   ", used_ocr=False, status="empty"),
    ]
    chunks = chunking_service.chunk_pages(pages, document_id="doc_456")
    assert len(chunks) == 1
    assert chunks[0]["page_number"] == 2
    assert chunks[0]["text"] == "Valid content here."


def test_long_paragraph_sentence_splitting():
    # Long text exceeding chunk size of 100
    long_para = "Sentence one is clear. Sentence two gives more details. Sentence three explains the conclusion."
    pages = [PageExtractionResult(page_number=1, text=long_para, used_ocr=False, status="success")]
    chunks = chunking_service.chunk_pages(pages, document_id="doc_789", chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 1
    for c in chunks:
        assert c["page_number"] == 1
        assert len(c["text"]) > 0
