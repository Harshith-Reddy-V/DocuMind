"""
Modular OCR service using Gemini multimodal vision.
Converts PDF pages into high-resolution images and transcribes readable text.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def ocr_page_image(image_bytes: bytes, gemini_provider=None) -> str:
    """
    Transcribe readable text from page image bytes using Gemini or injected provider.
    Never returns placeholder error text; raises or returns clean text.
    """
    if gemini_provider is not None:
        return gemini_provider.extract_text_from_image(image_bytes)

    # Lazy import to avoid circular dependency
    from app.services.gemini_service import get_gemini_provider
    provider = get_gemini_provider()
    return provider.extract_text_from_image(image_bytes)
