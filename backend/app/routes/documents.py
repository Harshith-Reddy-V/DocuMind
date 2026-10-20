"""
Document management and RAG query routes.
"""
import os
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from app.config import settings
from app.models.schemas import (
    UploadResponse,
    DocumentInfo,
    DocumentStatusResponse,
    QueryRequest,
    QueryResponse,
    SummarizeResponse,
    PaperAnalysisResponse,
    StudyGuideResponse,
)
from app.services import (
    ingestion_service,
    rag_service,
    document_store,
    vectorstore_service,
    summarization_service,
    analysis_service,
)
from app.utils.rate_limiter import check_rate_limit

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse, dependencies=[Depends(check_rate_limit)])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Accepts multipart PDF upload.
    Validates file content and size, safely stores the file, initializes status,
    and launches background ingestion.
    """
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Read content to validate size and magic bytes
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="The uploaded PDF file is empty.")

    # Check magic header bytes
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF format: file header does not match %PDF-.")

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed is {settings.MAX_FILE_SIZE_MB} MB.",
        )

    # Prevent filename collision (Bug 5)
    document_id = uuid.uuid4().hex[:12]
    original_basename = os.path.basename(file.filename)
    safe_basename = "".join(c for c in original_basename if c.isalnum() or c in "._- ").strip().replace(" ", "_")
    if not safe_basename:
        safe_basename = "document.pdf"

    # Store with unique ID prefix
    stored_filename = f"{document_id}_{safe_basename}"
    file_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    # Create initial persistent record in SQLite
    document_store.create_initial_document(
        document_id=document_id,
        filename=safe_basename,
        storage_path=file_path,
        status="processing",
        current_stage="validating",
    )

    # Schedule asynchronous ingestion pipeline (Bug 8)
    background_tasks.add_task(
        ingestion_service.process_document_pipeline,
        document_id=document_id,
        file_path=file_path,
        filename=safe_basename,
    )

    return UploadResponse(
        document_id=document_id,
        filename=safe_basename,
        status="processing",
        num_pages=0,
        num_chunks=0,
        used_ocr=False,
        warnings=[],
    )


@router.get("", response_model=List[DocumentInfo])
async def list_documents():
    """List all documents in workspace with their metadata and statuses."""
    docs = document_store.list_documents()
    return [DocumentInfo(**d) for d in docs]


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    """Retrieve document metadata by ID."""
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentInfo(**doc)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str):
    """Return stage-by-stage ingestion progress and warnings."""
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentStatusResponse(
        document_id=doc["document_id"],
        filename=doc["filename"],
        status=doc["status"],
        current_stage=doc.get("current_stage", "unknown"),
        progress_percent=doc.get("progress_percent", 0),
        num_pages=doc.get("num_pages", 0),
        num_chunks=doc.get("num_chunks", 0),
        used_ocr=doc.get("used_ocr", False),
        warnings=doc.get("warnings", []),
        error_message=doc.get("error_message"),
    )


@router.get("/{document_id}/file")
async def get_document_file(document_id: str):
    """Serve the original uploaded PDF after validating existence and storage ownership."""
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    file_path = doc.get("storage_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Original document file not found on disk.")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=doc.get("filename", "document.pdf")
    )


@router.post("/{document_id}/query", response_model=QueryResponse, dependencies=[Depends(check_rate_limit)])
async def query_document(document_id: str, request: QueryRequest):
    """Execute grounded question-answering with page citations."""
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.get("status") == "processing":
        raise HTTPException(status_code=409, detail="Document is still processing. Please wait until ready.")
    if doc.get("status") == "failed":
        raise HTTPException(status_code=400, detail=f"Document processing failed: {doc.get('error_message')}")

    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        history_dicts = [h.model_dump() for h in request.history] if request.history else []
        result = rag_service.answer_question(
            document_id=document_id,
            question=request.question.strip(),
            history=history_dicts,
            top_k=request.top_k,
            mode=request.mode or "document",
        )
        return QueryResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")


@router.post("/{document_id}/summarize", response_model=SummarizeResponse, dependencies=[Depends(check_rate_limit)])
async def summarize_document(document_id: str):
    """Generate hierarchical short and detailed summaries."""
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.get("status") != "ready":
        raise HTTPException(status_code=400, detail=f"Document is not ready (status: {doc.get('status')}).")

    try:
        summary_result = summarization_service.summarize_hierarchical(doc.get("full_text", ""))
        return SummarizeResponse(**summary_result)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@router.post("/{document_id}/analysis", response_model=PaperAnalysisResponse, dependencies=[Depends(check_rate_limit)])
async def analyze_document_overview(document_id: str):
    """Extract structured research paper overview."""
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.get("status") != "ready":
        raise HTTPException(status_code=400, detail=f"Document is not ready (status: {doc.get('status')}).")

    try:
        analysis_result = analysis_service.analyze_paper_document(document_id)
        return PaperAnalysisResponse(**analysis_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze document: {str(e)}")


@router.post("/{document_id}/study", response_model=StudyGuideResponse, dependencies=[Depends(check_rate_limit)])
async def get_study_guide(document_id: str):
    """Generate study guide materials (MCQs, viva questions, flashcards, key notes)."""
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.get("status") != "ready":
        raise HTTPException(status_code=400, detail=f"Document is not ready (status: {doc.get('status')}).")

    try:
        guide = analysis_service.generate_study_guide(document_id)
        return StudyGuideResponse(**guide)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate study guide: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Safely delete document metadata, ChromaDB vector collection, and uploaded file."""
    doc = document_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 1. Delete ChromaDB vector collection
    vectorstore_service.delete_document(document_id)

    # 2. Delete file from storage
    file_path = doc.get("storage_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    # 3. Delete metadata from SQLite
    document_store.delete_document(document_id)

    return {"status": "deleted"}
