"""
Persistent document metadata storage backed by SQLite and SQLAlchemy.
Replaces the previous in-memory registry.
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.database import SessionLocal, init_db
from app.models.database_models import DocumentModel

# Ensure database tables exist on module load
init_db()


def create_initial_document(
    document_id: str,
    filename: str,
    storage_path: str,
    status: str = "processing",
    current_stage: str = "validating"
) -> dict:
    """Create a new document record in the database."""
    with SessionLocal() as db:
        doc = DocumentModel(
            document_id=document_id,
            filename=filename,
            storage_path=storage_path,
            status=status,
            current_stage=current_stage,
            progress_percent=5,
            num_pages=0,
            num_chunks=0,
            used_ocr=False,
            warnings_json="[]",
            error_message=None,
            full_text="",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc.to_dict()


def update_progress(
    document_id: str,
    stage: str,
    progress_percent: int,
    status: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    error_message: Optional[str] = None,
    num_pages: Optional[int] = None,
    num_chunks: Optional[int] = None,
    used_ocr: Optional[bool] = None,
    full_text: Optional[str] = None
) -> Optional[dict]:
    """Update processing stage, progress, or completion metrics."""
    with SessionLocal() as db:
        doc = db.query(DocumentModel).filter(DocumentModel.document_id == document_id).first()
        if not doc:
            return None
        doc.current_stage = stage
        doc.progress_percent = progress_percent
        if status:
            doc.status = status
        if error_message is not None:
            doc.error_message = error_message
        if warnings is not None:
            existing = doc.warnings
            for w in warnings:
                if w not in existing:
                    existing.append(w)
            doc.warnings = existing
        if num_pages is not None:
            doc.num_pages = num_pages
        if num_chunks is not None:
            doc.num_chunks = num_chunks
        if used_ocr is not None:
            doc.used_ocr = used_ocr
        if full_text is not None:
            doc.full_text = full_text
        doc.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(doc)
        return doc.to_dict()


def save_document(
    document_id: str,
    filename: str,
    pages: list,
    chunks: list,
    used_ocr: bool,
    warnings: Optional[List[str]] = None,
    storage_path: Optional[str] = None
) -> dict:
    """Save or update document metadata when ingestion succeeds."""
    with SessionLocal() as db:
        doc = db.query(DocumentModel).filter(DocumentModel.document_id == document_id).first()
        full_text = "\n\n".join(p["text"] for p in pages if p.get("text"))
        if not doc:
            doc = DocumentModel(
                document_id=document_id,
                filename=filename,
                storage_path=storage_path or "",
                status="ready",
                current_stage="ready",
                progress_percent=100,
                num_pages=len(pages),
                num_chunks=len(chunks),
                used_ocr=used_ocr,
                warnings_json="[]",
                error_message=None,
                full_text=full_text,
            )
            if warnings:
                doc.warnings = warnings
            db.add(doc)
        else:
            doc.filename = filename
            doc.num_pages = len(pages)
            doc.num_chunks = len(chunks)
            doc.used_ocr = used_ocr
            doc.status = "ready"
            doc.current_stage = "ready"
            doc.progress_percent = 100
            doc.full_text = full_text
            if warnings:
                doc.warnings = warnings
            doc.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(doc)
        return doc.to_dict()


def get_document(document_id: str) -> Optional[dict]:
    """Retrieve document metadata by ID."""
    with SessionLocal() as db:
        doc = db.query(DocumentModel).filter(DocumentModel.document_id == document_id).first()
        return doc.to_dict() if doc else None


def list_documents() -> List[dict]:
    """List all documents ordered by creation time descending."""
    with SessionLocal() as db:
        docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
        return [doc.to_dict() for doc in docs]


def delete_document(document_id: str) -> bool:
    """Delete document metadata from SQLite."""
    with SessionLocal() as db:
        doc = db.query(DocumentModel).filter(DocumentModel.document_id == document_id).first()
        if doc:
            db.delete(doc)
            db.commit()
            return True
        return False
