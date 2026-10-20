"""
Workspace routes for multi-document operations.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.config import settings
from app.models.schemas import WorkspaceQueryRequest, QueryResponse, SourceReference
from app.services import document_store, rag_service, gemini_service
from app.services.gemini_service import EXACT_REFUSAL_SENTENCE
from app.utils.rate_limiter import check_rate_limit

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


@router.post("/query", response_model=QueryResponse, dependencies=[Depends(check_rate_limit)])
async def query_workspace(request: WorkspaceQueryRequest):
    """
    Query across multiple documents in the workspace.
    Each citation identifies its source document, page, and chunk.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Determine target documents
    all_docs = document_store.list_documents()
    ready_docs = [d for d in all_docs if d["status"] == "ready"]

    if request.document_ids:
        target_doc_ids = set(request.document_ids)
        target_docs = [d for d in ready_docs if d["document_id"] in target_doc_ids]
    else:
        target_docs = ready_docs

    if not target_docs:
        return QueryResponse(
            answer=EXACT_REFUSAL_SENTENCE,
            grounded=False,
            grounding_level="insufficient_evidence",
            sources=[]
        )

    # Retrieve chunks from each target document
    all_relevant_chunks: List[Dict[str, Any]] = []
    k_per_doc = request.top_k or settings.TOP_K

    for d in target_docs:
        try:
            chunks = rag_service.retrieve_relevant_chunks(
                document_id=d["document_id"],
                question=request.question.strip(),
                top_k=k_per_doc,
                threshold=settings.SIMILARITY_THRESHOLD,
            )
            for c in chunks:
                c["document_id"] = d["document_id"]
            all_relevant_chunks.extend(chunks)
        except Exception:
            continue

    if not all_relevant_chunks:
        return QueryResponse(
            answer=EXACT_REFUSAL_SENTENCE,
            grounded=False,
            grounding_level="insufficient_evidence",
            sources=[]
        )

    # Sort all retrieved chunks by score descending and take top K overall
    all_relevant_chunks.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = all_relevant_chunks[:settings.TOP_K]

    # Generate answer with multi-doc context
    generation = gemini_service.generate_grounded_answer(request.question.strip(), top_chunks)
    is_answerable = generation.get("answerable", False)
    answer_text = generation.get("answer", "").strip()
    cited_ids = generation.get("cited_chunk_ids", [])

    if (not is_answerable) or (EXACT_REFUSAL_SENTENCE.lower() in answer_text.lower()):
        return QueryResponse(
            answer=EXACT_REFUSAL_SENTENCE,
            grounded=False,
            grounding_level="insufficient_evidence",
            sources=[]
        )

    sources = [
        SourceReference(
            page=c.get("page_number", c.get("start_page", 1)),
            start_page=c.get("start_page", 1),
            end_page=c.get("end_page", 1),
            text=c["text"][:500],
            chunk_id=c["chunk_id"],
            score=c["score"],
            document_id=c.get("document_id"),
        )
        for c in top_chunks
        if not cited_ids or c["chunk_id"] in cited_ids
    ]

    return QueryResponse(
        answer=answer_text,
        grounded=True,
        grounding_level="strongly_supported" if top_chunks[0]["score"] >= 0.70 else "partially_supported",
        sources=sources
    )
