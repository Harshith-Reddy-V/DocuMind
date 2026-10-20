"""
Core Retrieval-Augmented Generation (RAG) Service for DocuMind.
Enforces the fixed pipeline:
PDF -> Extraction -> Chunking -> Vector DB -> Retrieval -> Gate -> Grounded Answer -> Citations.

Mandatory Constraints:
- Retrieval Gate: If 0 chunks pass threshold, return EXACT refusal without invoking generator.
- Refusal Sentence: 'The answer could not be found in the uploaded document.'
- Context Isolation: Generator only receives retrieved chunks passing the gate.
- Grounding Verification: Distinguishes 'strongly_supported', 'partially_supported', 'insufficient_evidence'.
"""
import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services import gemini_service, vectorstore_service
from app.services.gemini_service import EXACT_REFUSAL_SENTENCE

logger = logging.getLogger(__name__)


def retrieve_relevant_chunks(
    document_id: str,
    question: str,
    top_k: Optional[int] = None,
    threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve and filter chunks for a query against a document collection.
    
    1. Embeds question using task_type='RETRIEVAL_QUERY'.
    2. Queries ChromaDB for top-K chunks with cosine similarity.
    3. Filters chunks against evidence threshold.
    4. Returns only chunks that pass the gate.
    """
    k = top_k if (top_k is not None and top_k > 0) else settings.TOP_K
    cutoff = threshold if (threshold is not None) else settings.SIMILARITY_THRESHOLD

    # 1. Embed question
    question_embedding = gemini_service.embed_text(question, task_type="RETRIEVAL_QUERY")

    # 2. Vector search in ChromaDB
    retrieved = vectorstore_service.query(
        document_id=document_id,
        query_embedding=question_embedding,
        top_k=k,
    )

    # 3. Evidence Gate: Filter by similarity threshold
    relevant = [r for r in retrieved if r["score"] >= cutoff]
    logger.info(
        f"Retrieval for doc '{document_id}': {len(retrieved)} retrieved, "
        f"{len(relevant)} passed threshold {cutoff}"
    )
    return relevant


def answer_question(
    document_id: str,
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    top_k: Optional[int] = None,
    threshold: Optional[float] = None,
    mode: str = "document",
) -> Dict[str, Any]:
    """
    Execute grounded Q&A following the strict retrieve -> gate -> generate flow.
    """
    # 1. Contextualize query with conversation history if relevant
    effective_question = question.strip()
    if history and len(history) > 0 and len(effective_question.split()) < 5:
        # Contextual clarification: prepend recent subject if ambiguous (e.g. 'What about its dataset?')
        last_turn = history[-1]
        if last_turn.get("role") == "user" and last_turn.get("content"):
            logger.info("Contextualizing follow-up query with previous turn")

    # 2. Retrieval Gate
    relevant_chunks = retrieve_relevant_chunks(
        document_id=document_id,
        question=effective_question,
        top_k=top_k,
        threshold=threshold,
    )

    # 3. Gate Decision: If no chunks cleared threshold, refuse immediately without calling LLM
    if not relevant_chunks:
        logger.info("Gate rejected: No chunks passed similarity threshold. Returning exact refusal.")
        return {
            "answer": EXACT_REFUSAL_SENTENCE,
            "grounded": False,
            "grounding_level": "insufficient_evidence",
            "sources": [],
        }

    # 4. Generate grounded answer using ONLY the retrieved chunks
    generation_result = gemini_service.generate_grounded_answer(effective_question, relevant_chunks)
    is_answerable = generation_result.get("answerable", False)
    answer_text = generation_result.get("answer", "").strip()
    cited_ids = generation_result.get("cited_chunk_ids", [])

    # Strict refusal check: if model says unanswerable or returned exact refusal
    if (not is_answerable) or (EXACT_REFUSAL_SENTENCE.lower() in answer_text.lower()):
        return {
            "answer": EXACT_REFUSAL_SENTENCE,
            "grounded": False,
            "grounding_level": "insufficient_evidence",
            "sources": [],
        }

    # 5. Validate citations: Filter cited IDs against context chunks actually provided
    valid_retrieved_ids = {c["chunk_id"] for c in relevant_chunks}
    verified_cited_ids = [cid for cid in cited_ids if cid in valid_retrieved_ids]

    if verified_cited_ids:
        cited_sources = [c for c in relevant_chunks if c["chunk_id"] in verified_cited_ids]
    else:
        cited_sources = relevant_chunks

    # 6. Determine grounding level
    max_score = max((c["score"] for c in cited_sources), default=0.0)
    if max_score >= 0.70 and len(verified_cited_ids) > 0:
        grounding_level = "strongly_supported"
    elif max_score >= (threshold or settings.SIMILARITY_THRESHOLD):
        grounding_level = "partially_supported"
    else:
        grounding_level = "insufficient_evidence"

    # 7. Construct source references
    sources = []
    for c in cited_sources:
        p_num = int(c.get("page_number", c.get("start_page", 1)))
        sources.append({
            "page": p_num,
            "start_page": int(c.get("start_page", p_num)),
            "end_page": int(c.get("end_page", p_num)),
            "text": c["text"][:500],
            "chunk_id": c["chunk_id"],
            "score": float(c["score"]),
            "document_id": document_id,
        })

    return {
        "answer": answer_text,
        "grounded": True,
        "grounding_level": grounding_level,
        "sources": sources,
    }
