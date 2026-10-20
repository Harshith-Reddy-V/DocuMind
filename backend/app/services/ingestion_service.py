"""
Orchestrates the PDF ingestion pipeline:
validation -> extraction -> OCR fallback -> chunking -> embedding -> indexing -> registration.

Supports asynchronous background task processing and synchronous execution for tests.
Tracks stage-by-stage progress, OCR usage, and warnings in SQLite.
"""
import uuid
import logging
from typing import Dict, Any, Optional, List
from app.services import pdf_service, chunking_service, gemini_service, vectorstore_service, document_store

logger = logging.getLogger(__name__)


def process_document_pipeline(document_id: str, file_path: str, filename: str) -> Dict[str, Any]:
    """
    Executes the ingestion pipeline through distinct stages:
    validating -> extracting -> ocr (if needed) -> chunking -> embedding -> indexing -> ready.
    """
    warnings: List[str] = []
    used_ocr_overall = False

    try:
        # Stage 1: Validating
        document_store.update_progress(document_id, stage="validating", progress_percent=10, status="processing")
        pdf_service.validate_pdf(file_path)

        # Stage 2: Extracting (with OCR fallback where required)
        document_store.update_progress(document_id, stage="extracting", progress_percent=25)
        pages = pdf_service.extract_pages(file_path)

        # Inspect pages for OCR usage and warnings
        for p in pages:
            if p.used_ocr:
                used_ocr_overall = True
            if p.warning:
                warnings.append(p.warning)

        if used_ocr_overall:
            document_store.update_progress(document_id, stage="ocr", progress_percent=40, used_ocr=True, warnings=warnings)

        # Validate that there is at least some usable text
        usable_pages = [p for p in pages if p.text and p.text.strip()]
        if not usable_pages:
            raise ValueError("No extractable text found in this document (pages empty or unreadable).")

        # Stage 3: Chunking
        document_store.update_progress(document_id, stage="chunking", progress_percent=55)
        chunks = chunking_service.chunk_pages(pages, document_id)
        if not chunks:
            raise ValueError("No text chunks generated from extracted content.")

        # Stage 4: Embedding
        document_store.update_progress(document_id, stage="embedding", progress_percent=75)
        texts = [c["text"] for c in chunks]
        embeddings = gemini_service.embed_batch(texts, task_type="RETRIEVAL_DOCUMENT")

        # Stage 5: Indexing
        document_store.update_progress(document_id, stage="indexing", progress_percent=90)
        vectorstore_service.add_chunks(document_id, chunks, embeddings)

        # Stage 6: Ready - Register final metadata in persistent SQLite
        pages_dicts = [p.to_dict() for p in pages]
        doc_record = document_store.save_document(
            document_id=document_id,
            filename=filename,
            pages=pages_dicts,
            chunks=chunks,
            used_ocr=used_ocr_overall,
            warnings=warnings,
            storage_path=file_path
        )
        logger.info(f"Document {document_id} successfully ingested: {len(pages)} pages, {len(chunks)} chunks.")
        return doc_record

    except Exception as e:
        logger.error(f"Ingestion pipeline failed for document {document_id}: {e}", exc_info=True)
        # Clean up partially created vector collections
        try:
            vectorstore_service.delete_document(document_id)
        except Exception:
            pass

        sanitized_error = str(e)
        document_store.update_progress(
            document_id=document_id,
            stage="failed",
            progress_percent=0,
            status="failed",
            error_message=sanitized_error,
            warnings=warnings
        )
        raise e


def ingest_pdf(file_path: str, filename: str, document_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Synchronous entry point primarily used by tests or sync routes.
    """
    doc_id = document_id or uuid.uuid4().hex[:12]
    document_store.create_initial_document(
        document_id=doc_id,
        filename=filename,
        storage_path=file_path,
        status="processing",
        current_stage="validating"
    )
    return process_document_pipeline(doc_id, file_path, filename)
