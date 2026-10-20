"""
Handles PDF validation and text extraction with PyMuPDF and OCR fallback.
"""
import os
import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
import pymupdf
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class PageExtractionResult:
    page_number: int
    text: str
    used_ocr: bool
    status: str  # "success", "empty", "ocr_fallback", "failed"
    warning: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def validate_pdf(file_path: str) -> None:
    """
    Validates PDF file existence, magic bytes, structure, and readability.
    Raises ValueError with a clear, safe message if invalid.
    """
    if not os.path.exists(file_path):
        raise ValueError("File does not exist.")

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError("The uploaded PDF file is empty (0 bytes).")

    # Validate header magic bytes
    with open(file_path, "rb") as f:
        header = f.read(5)
        if header != b"%PDF-":
            raise ValueError("Invalid PDF format: Missing %PDF- header.")

    # Validate with PyMuPDF
    try:
        doc = pymupdf.open(file_path)
    except Exception as e:
        raise ValueError(f"Corrupted or unreadable PDF: {str(e)}")

    try:
        if doc.is_encrypted:
            raise ValueError("Password-protected PDFs are not supported.")
        if len(doc) == 0:
            raise ValueError("PDF contains no pages.")
    finally:
        doc.close()


def count_pages(file_path: str) -> int:
    """Count total pages in PDF."""
    validate_pdf(file_path)
    doc = pymupdf.open(file_path)
    try:
        return len(doc)
    finally:
        doc.close()


def extract_pages(
    file_path: str,
    ocr_fn: Optional[Callable[[bytes], str]] = None
) -> List[PageExtractionResult]:
    """
    Extract text page by page.
    Falls back to OCR for image-only or low-text pages without indexing error placeholders.
    """
    validate_pdf(file_path)
    doc = pymupdf.open(file_path)
    results: List[PageExtractionResult] = []

    try:
        for page_index in range(len(doc)):
            page_num = page_index + 1
            page = doc[page_index]
            text = page.get_text("text").strip()

            if len(text) >= settings.OCR_MIN_CHARS:
                results.append(PageExtractionResult(
                    page_number=page_num,
                    text=text,
                    used_ocr=False,
                    status="success",
                    warning=None
                ))
            else:
                # Page has insufficient text; attempt OCR fallback
                logger.info(f"Page {page_num} has only {len(text)} chars; attempting OCR.")
                try:
                    pix = page.get_pixmap(dpi=settings.OCR_DPI)
                    image_bytes = pix.tobytes("png")

                    if ocr_fn is not None:
                        ocr_text = ocr_fn(image_bytes)
                    else:
                        from app.services.ocr_service import ocr_page_image
                        ocr_text = ocr_page_image(image_bytes)

                    ocr_clean = (ocr_text or "").strip()
                    if ocr_clean:
                        results.append(PageExtractionResult(
                            page_number=page_num,
                            text=ocr_clean,
                            used_ocr=True,
                            status="ocr_fallback",
                            warning=None
                        ))
                    else:
                        # OCR ran but produced no text (blank page)
                        results.append(PageExtractionResult(
                            page_number=page_num,
                            text="",
                            used_ocr=True,
                            status="empty",
                            warning=f"Page {page_num} produced no readable text after OCR."
                        ))
                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num}: {e}")
                    # NEVER index error placeholder string!
                    results.append(PageExtractionResult(
                        page_number=page_num,
                        text="",
                        used_ocr=True,
                        status="failed",
                        warning=f"OCR failed on page {page_num}: {str(e)}"
                    ))
    finally:
        doc.close()

    return results
