"""
Patent Feasibility Analyzer Service.
Orchestrates multi-paper prior-art retrieval, idea decomposition,
grounded comparative evaluation via Gemini, and persistence.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.config import settings
from app.models.schemas import (
    PatentAnalysisRequest,
    PatentFeasibilityReport,
    PatentAnalysisSummaryItem,
    PaperComparison,
    FindingEvidence,
    PATENT_DISCLAIMER,
)
from app.services import (
    document_store,
    vectorstore_service,
    rag_service,
    gemini_service,
    patent_store,
)

logger = logging.getLogger(__name__)


INSUFFICIENT_EVIDENCE_APPROACH = (
    "Insufficient evidence in the supplied excerpts to determine the paper's relevant approach."
)


def _find_matched_paper(
    doc_id: Optional[str],
    title: Optional[str],
    paper_evidence_list: List[Dict[str, Any]],
    index: int,
) -> Dict[str, Any]:
    if doc_id:
        for p in paper_evidence_list:
            if p.get("document_id") == doc_id:
                return p
    if title:
        for p in paper_evidence_list:
            if p.get("paper_title") == title:
                return p
    if 0 <= index < len(paper_evidence_list):
        return paper_evidence_list[index]
    return {}


def _normalize_paper_comparison(
    raw: Any,
    paper_evidence_list: List[Dict[str, Any]],
    index: int,
) -> PaperComparison:
    if isinstance(raw, PaperComparison):
        return raw

    if not isinstance(raw, dict):
        raw = {}

    matched = _find_matched_paper(raw.get("document_id"), raw.get("paper_title"), paper_evidence_list, index)
    doc_id = raw.get("document_id") or matched.get("document_id") or f"doc_{index + 1}"
    paper_title = raw.get("paper_title") or matched.get("paper_title") or f"Document {index + 1}"

    # Robust handling for required relevant_approach
    relevant_approach = raw.get("relevant_approach")
    if relevant_approach is None or not str(relevant_approach).strip():
        # Derive factual approach from retrieved source evidence if available
        chunks = matched.get("chunks", [])
        usable_chunks = [c for c in chunks if isinstance(c, dict) and c.get("text", "").strip()]
        if usable_chunks:
            chunk_obj = usable_chunks[0]
            first_text = " ".join(chunk_obj.get("text", "").split())[:180]
            page = chunk_obj.get("page_number", chunk_obj.get("start_page", 1))
            relevant_approach = f'Disclosed approach in excerpt (Page {page}): "{first_text}"'
        else:
            relevant_approach = INSUFFICIENT_EVIDENCE_APPROACH
    else:
        relevant_approach = str(relevant_approach).strip()

    # Overlapping features
    overlapping_features = raw.get("overlapping_features")
    if not isinstance(overlapping_features, list):
        overlapping_features = [str(overlapping_features)] if overlapping_features else []
    else:
        overlapping_features = [str(x) for x in overlapping_features if str(x).strip()]

    # Differences
    differences = raw.get("differences")
    if not isinstance(differences, list):
        differences = [str(differences)] if differences else []
    else:
        differences = [str(x) for x in differences if str(x).strip()]

    # Strongest evidence
    strongest_evidence = raw.get("strongest_evidence")
    if not strongest_evidence or not isinstance(strongest_evidence, str):
        chunks = matched.get("chunks", [])
        valid_chunks = [c for c in chunks if isinstance(c, dict) and c.get("text", "").strip()]
        strongest_evidence = valid_chunks[0].get("text", "")[:180] if valid_chunks else ""

    # Page references
    raw_pages = raw.get("page_references")
    page_references: List[int] = []
    if isinstance(raw_pages, list):
        for p in raw_pages:
            try:
                page_references.append(int(p))
            except (ValueError, TypeError):
                continue
    if not page_references and matched.get("chunks"):
        for c in matched.get("chunks", []):
            if isinstance(c, dict):
                pnum = c.get("page_number", c.get("start_page"))
                if pnum is not None:
                    try:
                        p_int = int(pnum)
                        if p_int not in page_references:
                            page_references.append(p_int)
                    except (ValueError, TypeError):
                        pass

    remaining_uncertainties = raw.get("remaining_uncertainties")
    if remaining_uncertainties is None or not isinstance(remaining_uncertainties, str):
        remaining_uncertainties = ""

    return PaperComparison(
        document_id=str(doc_id),
        paper_title=str(paper_title),
        relevant_approach=relevant_approach,
        overlapping_features=overlapping_features,
        differences=differences,
        strongest_evidence=strongest_evidence,
        page_references=page_references,
        remaining_uncertainties=remaining_uncertainties,
    )


def _normalize_finding_evidence(
    raw: Any,
    paper_evidence_list: List[Dict[str, Any]],
    index: int,
) -> Optional[FindingEvidence]:
    if isinstance(raw, FindingEvidence):
        return raw

    if not isinstance(raw, dict):
        return None

    finding = raw.get("finding")
    if not finding or not str(finding).strip():
        return None

    matched = _find_matched_paper(None, raw.get("source_paper_title"), paper_evidence_list, index)
    source_title = raw.get("source_paper_title") or matched.get("paper_title") or f"Document {index + 1}"
    supporting = raw.get("supporting_evidence") or ""
    page_num = raw.get("page_number")
    if page_num is not None:
        try:
            page_num = int(page_num)
        except (ValueError, TypeError):
            page_num = None

    confidence = raw.get("confidence", "medium")
    if confidence not in ["high", "medium", "low"]:
        confidence = "medium"

    return FindingEvidence(
        finding=str(finding).strip(),
        explanation=str(raw.get("explanation", "")).strip(),
        supporting_evidence=str(supporting).strip(),
        source_paper_title=str(source_title).strip(),
        page_number=page_num,
        confidence=confidence,
        is_direct_support=bool(raw.get("is_direct_support", True)),
    )


def _ensure_str_list(val: Any, default: List[str]) -> List[str]:
    if isinstance(val, list):
        return [str(x) for x in val if str(x).strip()]
    elif isinstance(val, str) and val.strip():
        return [val.strip()]
    return default


def run_patent_feasibility_analysis(request: PatentAnalysisRequest) -> PatentFeasibilityReport:
    """
    Executes an end-to-end patent feasibility evaluation for a user's proposed invention idea
    against one or more uploaded/selected research papers.
    """
    analysis_id = uuid.uuid4().hex[:12]
    now_str = datetime.now(timezone.utc).isoformat()

    # 1. Resolve and validate target documents
    paper_evidence_list: List[Dict[str, Any]] = []
    target_doc_ids = request.document_ids or []

    for doc_id in target_doc_ids:
        doc = document_store.get_document(doc_id)
        if not doc:
            logger.warning(f"Patent analysis requested non-existent document ID: {doc_id}")
            continue

        if doc.get("status") != "ready":
            logger.info(f"Skipping document {doc_id} because status is '{doc.get('status')}'")
            continue

        filename = doc.get("filename", f"paper_{doc_id}.pdf")

        # Multi-query retrieval strategy:
        # Query A: Problem & title domain terms
        # Query B: Technical solution mechanisms
        # Query C: Specific differentiation claims
        retrieved_chunks: List[Dict[str, Any]] = []
        queries = [
            f"{request.title}: {request.problem_solved}",
            request.technical_solution,
        ]
        if request.differentiation_notes and request.differentiation_notes.strip():
            queries.append(request.differentiation_notes.strip())

        seen_chunk_ids = set()
        for q in queries:
            try:
                # Primary retrieval with evidence threshold
                chunks = rag_service.retrieve_relevant_chunks(
                    document_id=doc_id,
                    question=q,
                    top_k=settings.TOP_K,
                    threshold=settings.SIMILARITY_THRESHOLD,
                )
                # If gate rejects all chunks, fall back to top matches so comparison has evidence
                if not chunks:
                    q_emb = gemini_service.embed_text(q, task_type="RETRIEVAL_QUERY")
                    raw_chunks = vectorstore_service.query(
                        document_id=doc_id,
                        query_embedding=q_emb,
                        top_k=3,
                    )
                    chunks = raw_chunks

                for c in chunks:
                    cid = c.get("chunk_id")
                    if cid and cid not in seen_chunk_ids:
                        seen_chunk_ids.add(cid)
                        retrieved_chunks.append(c)
            except Exception as e:
                logger.warning(f"Error querying doc {doc_id} with query '{q}': {e}")

        paper_evidence_list.append({
            "document_id": doc_id,
            "paper_title": filename,
            "chunks": retrieved_chunks,
        })

    # 2. Prepare structured idea payload
    idea_data = {
        "title": request.title,
        "idea_description": request.idea_description,
        "problem_solved": request.problem_solved,
        "technical_solution": request.technical_solution,
        "differentiation_notes": request.differentiation_notes or "",
        "target_industry": request.target_industry,
        "jurisdiction": request.jurisdiction or "United States",
    }

    # 3. Call Gemini provider (or mock provider in test mode)
    llm_result = gemini_service.analyze_patent_feasibility(
        idea_data=idea_data,
        paper_evidence_list=paper_evidence_list,
    )

    # 4. Construct validated PatentFeasibilityReport
    if not isinstance(llm_result, dict):
        logger.warning(f"LLM returned non-dict result: {type(llm_result)}. Initializing safe fallback.")
        llm_result = {}

    paper_comparisons_raw = llm_result.get("paper_comparisons")
    paper_comparisons: List[PaperComparison] = []
    if isinstance(paper_comparisons_raw, list):
        for idx, pc in enumerate(paper_comparisons_raw):
            try:
                comp = _normalize_paper_comparison(pc, paper_evidence_list, idx)
                paper_comparisons.append(comp)
            except Exception as e:
                logger.warning(f"Error normalizing PaperComparison {idx}: {e}", exc_info=True)
    elif paper_evidence_list:
        # LLM response had malformed or non-list paper_comparisons
        for idx, p in enumerate(paper_evidence_list):
            try:
                comp = _normalize_paper_comparison({}, paper_evidence_list, idx)
                paper_comparisons.append(comp)
            except Exception as e:
                logger.warning(f"Error creating fallback PaperComparison for doc {p.get('document_id')}: {e}", exc_info=True)

    prior_art_raw = llm_result.get("prior_art_findings")
    prior_art_findings: List[FindingEvidence] = []
    if isinstance(prior_art_raw, list):
        for idx, pa in enumerate(prior_art_raw):
            try:
                norm_finding = _normalize_finding_evidence(pa, paper_evidence_list, idx)
                if norm_finding:
                    prior_art_findings.append(norm_finding)
            except Exception as e:
                logger.warning(f"Error normalizing FindingEvidence {idx}: {e}")

    valid_assessments = [
        "Potentially worth further investigation",
        "Significant overlap found in supplied papers",
        "Insufficient evidence to assess",
    ]
    assessment = llm_result.get("preliminary_assessment")
    if assessment not in valid_assessments:
        if not paper_evidence_list or sum(len(p.get("chunks", [])) for p in paper_evidence_list) == 0:
            assessment = "Insufficient evidence to assess"
        else:
            assessment = "Potentially worth further investigation"

    explanation = llm_result.get("preliminary_assessment_explanation")
    if not explanation or not isinstance(explanation, str):
        if assessment == "Insufficient evidence to assess":
            explanation = "Insufficient evidence: none of the supplied documents contain sufficient technical details to evaluate the proposed invention."
        else:
            explanation = "Evaluation completed based on available research paper disclosures."

    exec_summary = llm_result.get("executive_summary")
    if not exec_summary or not isinstance(exec_summary, str):
        exec_summary = f"Patent feasibility analysis for '{request.title}' based on {len(paper_evidence_list)} supplied reference document(s)."

    patentability_concerns = llm_result.get("patentability_concerns")
    if not isinstance(patentability_concerns, dict):
        patentability_concerns = {
            "novelty": "Requires comparison against published patent records.",
            "inventive_step": "Must demonstrate non-obvious technical effect over baseline literature.",
            "subject_matter_eligibility": f"Statutory technical contribution must be shown under {request.jurisdiction or 'United States'} patent guidelines."
        }

    report = PatentFeasibilityReport(
        analysis_id=analysis_id,
        title=request.title,
        executive_summary=exec_summary,
        preliminary_assessment=assessment,
        preliminary_assessment_explanation=explanation,
        idea_decomposition=_ensure_str_list(
            llm_result.get("idea_decomposition"),
            [
                f"Core problem: {request.problem_solved[:80]}",
                f"Proposed solution: {request.technical_solution[:80]}",
            ]
        ),
        paper_comparisons=paper_comparisons,
        potentially_differentiating_features=_ensure_str_list(
            llm_result.get("potentially_differentiating_features"),
            [request.differentiation_notes] if request.differentiation_notes else []
        ),
        prior_art_findings=prior_art_findings,
        technical_feasibility_risks=_ensure_str_list(
            llm_result.get("technical_feasibility_risks"),
            ["Technical implementation feasibility requires empirical bench testing."]
        ),
        research_gaps=_ensure_str_list(
            llm_result.get("research_gaps"),
            ["Additional prior art search across commercial patent registers recommended."]
        ),
        patentability_concerns=patentability_concerns,
        suggested_next_steps=_ensure_str_list(
            llm_result.get("suggested_next_steps"),
            [
                "Develop prototype or simulation to validate technical performance.",
                "Conduct prior art searches in official patent databases (e.g., USPTO, EPO).",
                "Consult a patent attorney before public disclosure."
            ]
        ),
        disclaimer=PATENT_DISCLAIMER,
        external_search_performed=False,
        jurisdiction=request.jurisdiction or "United States",
        target_industry=request.target_industry,
        paper_ids=[p["document_id"] for p in paper_evidence_list],
        created_at=now_str,
    )

    # 5. Persist analysis to SQLite database
    try:
        patent_store.save_patent_analysis(
            analysis_id=report.analysis_id,
            title=report.title,
            idea_description=request.idea_description,
            problem_solved=request.problem_solved,
            technical_solution=request.technical_solution,
            differentiation_notes=request.differentiation_notes or "",
            target_industry=request.target_industry,
            jurisdiction=request.jurisdiction or "United States",
            paper_ids=report.paper_ids,
            report=report.model_dump(),
            preliminary_assessment=report.preliminary_assessment,
        )
    except Exception as e:
        logger.error(f"Failed to persist patent analysis {analysis_id}: {e}")

    return report


def get_patent_analysis(analysis_id: str) -> Optional[PatentFeasibilityReport]:
    """Retrieve a previously saved patent analysis by ID."""
    data = patent_store.get_patent_analysis(analysis_id)
    if not data:
        return None
    return PatentFeasibilityReport(**data)


def list_patent_analyses() -> List[PatentAnalysisSummaryItem]:
    """List summary items of all saved patent analyses."""
    records = patent_store.list_patent_analyses()
    return [PatentAnalysisSummaryItem(**r) for r in records]


def delete_patent_analysis(analysis_id: str) -> bool:
    """Delete a saved patent analysis by ID."""
    return patent_store.delete_patent_analysis(analysis_id)
