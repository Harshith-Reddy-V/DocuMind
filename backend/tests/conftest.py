"""
Test fixtures and configuration for DocuMind backend tests.
Ensures tests run deterministically without requiring a real Gemini API key.
"""
import os
import shutil
import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.database import engine, Base, SessionLocal, init_db
from app.services import gemini_service, document_store, vectorstore_service
from app.services.gemini_service import MockGeminiProvider
from app.utils.rate_limiter import reset_rate_limits
from app.main import app


@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """
    Isolate test storage, vector database, and SQLite database for each test.
    Injects deterministic MockGeminiProvider.
    """
    test_data_dir = tmp_path / "data"
    test_upload_dir = test_data_dir / "uploads"
    test_vector_dir = test_data_dir / "chroma"
    test_db_file = test_data_dir / "test_documind.db"

    test_upload_dir.mkdir(parents=True, exist_ok=True)
    test_vector_dir.mkdir(parents=True, exist_ok=True)

    # Patch settings
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(test_upload_dir))
    monkeypatch.setattr(settings, "VECTOR_DB_DIR", str(test_vector_dir))
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{test_db_file}")
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 100)

    # Re-initialize test database
    init_db()

    # Reset vector client to use new temp directory
    vectorstore_service._client = None

    # Inject mock gemini provider
    mock_provider = MockGeminiProvider()
    gemini_service.set_gemini_provider(mock_provider)

    # Reset rate limits
    reset_rate_limits()

    yield {
        "mock_provider": mock_provider,
        "upload_dir": str(test_upload_dir),
        "vector_dir": str(test_vector_dir),
        "db_file": str(test_db_file),
    }

    # Teardown
    gemini_service.reset_gemini_provider()
    vectorstore_service._client = None
    reset_rate_limits()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_pdf():
    """Helper to generate PDFs with custom text or image content."""
    import pymupdf

    def _create(file_path: str, pages_content: list, encrypted: bool = False, password: str = "pass123"):
        doc = pymupdf.open()
        for content in pages_content:
            page = doc.new_page()
            if isinstance(content, str):
                page.insert_text((50, 72), content, fontsize=11)
            elif isinstance(content, bytes) or content is None:
                # Scanned image-only page (no text)
                pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 150, 150), 1)
                page.insert_image(page.rect, pixmap=pix)

        if encrypted:
            doc.save(file_path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw=password)
        else:
            doc.save(file_path)
        doc.close()
        return file_path

    return _create
