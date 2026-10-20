"""
Hierarchical / Map-Reduce summarization service for academic documents.
Prevents single oversized generation calls by summarizing in bounded stages.
"""
import logging
from typing import Dict, List, Any, Optional
from app.services import gemini_service

logger = logging.getLogger(__name__)

BATCH_CHAR_LIMIT = 4000


def summarize_hierarchical(full_text: str, chunks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Produce short and detailed summaries using hierarchical map-reduce summarization.
    """
    clean_text = (full_text or "").strip()
    if not clean_text:
        return {
            "short_summary": "Document contains no text to summarize.",
            "detailed_summary": "Document contains no text to summarize.",
            "section_summaries": []
        }

    # If the document is small enough, a single pass is safe and accurate
    if len(clean_text) <= BATCH_CHAR_LIMIT:
        summary_result = gemini_service.generate_summary(clean_text)
        return {
            "short_summary": summary_result["short_summary"],
            "detailed_summary": summary_result["detailed_summary"],
            "section_summaries": []
        }

    # Step 1: Chunk text into manageable units (Map phase)
    units: List[str] = []
    if chunks and len(chunks) > 0:
        current_unit = ""
        for c in chunks:
            c_text = c.get("text", "")
            if len(current_unit) + len(c_text) < BATCH_CHAR_LIMIT:
                current_unit += ("\n\n" if current_unit else "") + c_text
            else:
                if current_unit:
                    units.append(current_unit)
                current_unit = c_text
        if current_unit:
            units.append(current_unit)
    else:
        # Split text by paragraphs into blocks of BATCH_CHAR_LIMIT
        paras = clean_text.split("\n\n")
        current_unit = ""
        for p in paras:
            if len(current_unit) + len(p) < BATCH_CHAR_LIMIT:
                current_unit += ("\n\n" if current_unit else "") + p
            else:
                if current_unit:
                    units.append(current_unit)
                current_unit = p
        if current_unit:
            units.append(current_unit)

    # Step 2: Generate intermediate summaries for each unit
    logger.info(f"Hierarchical summarization: Processing {len(units)} units")
    intermediate_summaries: List[str] = []
    for i, unit in enumerate(units):
        try:
            inter = gemini_service.generate_summary(unit)
            unit_summary = inter.get("short_summary") or inter.get("detailed_summary") or ""
            if unit_summary:
                intermediate_summaries.append(f"Section {i+1} Summary:\n{unit_summary}")
        except Exception as e:
            logger.warning(f"Intermediate summarization failed for unit {i+1}: {e}")
            # Include truncated snippet so context is not completely lost
            intermediate_summaries.append(f"Section {i+1} Excerpt:\n{unit[:400]}")

    # Step 3: Combine intermediate summaries (Reduce phase)
    combined_context = "\n\n".join(intermediate_summaries)
    final_result = gemini_service.generate_summary(combined_context)

    # Step 4: Extract optional section summaries
    section_summaries = []
    for i, inter in enumerate(intermediate_summaries):
        section_summaries.append({
            "heading": f"Section {i+1}",
            "content": inter.replace(f"Section {i+1} Summary:\n", "").strip()
        })

    return {
        "short_summary": final_result["short_summary"],
        "detailed_summary": final_result["detailed_summary"],
        "section_summaries": section_summaries
    }
