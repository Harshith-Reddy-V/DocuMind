"""
Tests for PDF validation, page-wise extraction, OCR fallback, and error handling.
"""
import os
import pytest
from app.services import pdf_service


def test_valid_pdf_extraction(tmp_path, make_pdf):
    pdf_path = str(tmp_path / "valid.pdf")
    make_pdf(pdf_path, [
        "Page 1: Introduction to neural network architectures.",
        "Page 2: The proposed system uses a CNN model."
    ])

    results = pdf_service.extract_pages(pdf_path)
    assert len(results) == 2
    assert results[0].page_number == 1
    assert "Introduction" in results[0].text
    assert not results[0].used_ocr
    assert results[0].status == "success"

    assert results[1].page_number == 2
    assert "CNN model" in results[1].text
    assert not results[1].used_ocr


def test_scanned_pdf_ocr_fallback(tmp_path, make_pdf):
    """Scenario D: Scanned/image-only PDF triggers OCR fallback."""
    pdf_path = str(tmp_path / "scanned.pdf")
    # Content is None -> creates page with only an image, no text layer
    make_pdf(pdf_path, [None])

    results = pdf_service.extract_pages(pdf_path)
    assert len(results) == 1
    page = results[0]
    assert page.page_number == 1
    assert page.used_ocr is True
    assert page.status == "ocr_fallback"
    assert "CNN model" in page.text


def test_ocr_failure_does_not_index_placeholder(tmp_path, make_pdf):
    """Bug 3: OCR failure must NOT produce error placeholders in the text."""
    pdf_path = str(tmp_path / "scanned_fail.pdf")
    make_pdf(pdf_path, [None])

    def failing_ocr(image_bytes: bytes) -> str:
        raise RuntimeError("OCR device failure")

    results = pdf_service.extract_pages(pdf_path, ocr_fn=failing_ocr)
    assert len(results) == 1
    page = results[0]
    assert page.used_ocr is True
    assert page.status == "failed"
    # Never index placeholder strings!
    assert page.text == ""
    assert "[OCR failed" not in page.text
    assert page.warning is not None
    assert "OCR failed" in page.warning


def test_invalid_pdf_handling(tmp_path, make_pdf):
    """Scenario E: Test empty, non-pdf, corrupted, and encrypted files."""
    # 1. Non-existent file
    with pytest.raises(ValueError, match="does not exist"):
        pdf_service.validate_pdf(str(tmp_path / "missing.pdf"))

    # 2. Empty (0-byte) file
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        pdf_service.validate_pdf(str(empty_file))

    # 3. Invalid header
    corrupt_header = tmp_path / "bad_header.pdf"
    corrupt_header.write_bytes(b"NOT_A_PDF_CONTENT")
    with pytest.raises(ValueError, match="Missing %PDF- header"):
        pdf_service.validate_pdf(str(corrupt_header))

    # 4. Password-protected PDF
    encrypted_pdf = str(tmp_path / "encrypted.pdf")
    make_pdf(encrypted_pdf, ["Secret text"], encrypted=True, password="secret")
    with pytest.raises(ValueError, match="Password-protected"):
        pdf_service.validate_pdf(encrypted_pdf)
