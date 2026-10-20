"""
Pydantic schemas for request and response validation.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    num_pages: int = 0
    num_chunks: int = 0
    used_ocr: bool = False
    warnings: List[str] = Field(default_factory=list)


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    num_pages: int
    num_chunks: int
    status: str
    used_ocr: bool = False
    current_stage: Optional[str] = None
    progress_percent: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    created_at: Optional[str] = None


class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str  # processing, ready, failed
    current_stage: str  # validating, extracting, ocr, chunking, embedding, indexing, ready, failed
    progress_percent: int
    num_pages: int
    num_chunks: int
    used_ocr: bool
    warnings: List[str]
    error_message: Optional[str] = None


class QueryHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    question: str
    mode: Optional[Literal["document", "research"]] = "document"
    history: Optional[List[QueryHistoryItem]] = Field(default_factory=list)
    top_k: Optional[int] = None


class WorkspaceQueryRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None
    mode: Optional[Literal["document", "research"]] = "document"
    top_k: Optional[int] = None


class SourceReference(BaseModel):
    page: int
    text: str
    chunk_id: str
    score: float
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    document_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    grounded: bool
    grounding_level: Literal["strongly_supported", "partially_supported", "insufficient_evidence"] = "strongly_supported"
    sources: List[SourceReference]


class SectionSummary(BaseModel):
    heading: str
    content: str


class SummarizeResponse(BaseModel):
    short_summary: str
    detailed_summary: str
    section_summaries: Optional[List[SectionSummary]] = None


class PaperAnalysisResponse(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    keywords: List[str]
    methodology: str
    dataset: str
    results: str
    limitations: str
    future_work: str
    references: List[str]


class MCQItem(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str


class FlashcardItem(BaseModel):
    front: str
    back: str


class VivaQuestionItem(BaseModel):
    question: str
    suggested_answer: str


class StudyGuideResponse(BaseModel):
    mcqs: List[MCQItem]
    viva_questions: List[VivaQuestionItem]
    flashcards: List[FlashcardItem]
    key_notes: List[str]


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


# ---------------------------------------------------------------------------
# Patent Feasibility Analyzer Schemas
# ---------------------------------------------------------------------------

PATENT_DISCLAIMER = (
    "This report is an AI-assisted preliminary research tool, not a legal opinion or a determination "
    "of patentability. It analyzes the information and sources available to it and may miss relevant "
    "prior art. Patentability requires a full assessment under applicable law, including relevant "
    "prior art and jurisdiction-specific requirements. Consult a qualified patent professional before "
    "making filing decisions."
)


class FindingEvidence(BaseModel):
    finding: str = Field(description="Summary of the specific finding or overlap")
    explanation: str = Field(default="", description="Detailed explanation of the technical alignment or divergence")
    supporting_evidence: str = Field(description="Exact or closely paraphrased excerpt from the source paper")
    source_paper_title: str = Field(description="Title or filename of the source research paper")
    page_number: Optional[int] = Field(default=None, description="Page number where evidence is found")
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Confidence in evidence strength (not probability of patent approval)"
    )
    is_direct_support: bool = Field(
        default=True,
        description="True if directly supported by extracted text; False if an AI inference"
    )


class PaperComparison(BaseModel):
    document_id: str = Field(description="Document ID of the compared paper")
    paper_title: str = Field(description="Title or filename of the compared paper")
    relevant_approach: str = Field(description="Summary of the paper's core technical approach")
    overlapping_features: List[str] = Field(default_factory=list, description="Features shared with the user's idea")
    differences: List[str] = Field(default_factory=list, description="Concrete differences from the user's idea")
    strongest_evidence: str = Field(default="", description="The single strongest supporting passage from this paper")
    page_references: List[int] = Field(default_factory=list, description="Relevant page numbers")
    remaining_uncertainties: str = Field(default="", description="Uncertainties or technical details not disclosed")


class PatentFeasibilityReport(BaseModel):
    analysis_id: Optional[str] = None
    title: str = Field(description="Project idea title")
    executive_summary: str = Field(description="Short overview of the idea and core findings")
    preliminary_assessment: Literal[
        "Potentially worth further investigation",
        "Significant overlap found in supplied papers",
        "Insufficient evidence to assess"
    ] = Field(description="Preliminary assessment label")
    preliminary_assessment_explanation: str = Field(
        description="Detailed rationale for the chosen preliminary assessment label"
    )
    idea_decomposition: List[str] = Field(
        default_factory=list,
        description="Decomposition of the proposed idea into discrete technical features"
    )
    paper_comparisons: List[PaperComparison] = Field(
        default_factory=list,
        description="Detailed paper-by-paper comparison against each supplied document"
    )
    potentially_differentiating_features: List[str] = Field(
        default_factory=list,
        description="Aspects appearing distinct from the supplied papers (candidates for investigation)"
    )
    prior_art_findings: List[FindingEvidence] = Field(
        default_factory=list,
        description="Specific findings with evidence citations and confidence levels"
    )
    technical_feasibility_risks: List[str] = Field(
        default_factory=list,
        description="Implementation hurdles, dependencies, and engineering uncertainties"
    )
    research_gaps: List[str] = Field(
        default_factory=list,
        description="Limitations of existing papers and opportunities for novelty"
    )
    patentability_concerns: Dict[str, str] = Field(
        default_factory=dict,
        description="Potential concerns regarding novelty, inventive step, and subject matter eligibility"
    )
    suggested_next_steps: List[str] = Field(
        default_factory=list,
        description="Concrete, actionable recommendations for the inventor"
    )
    disclaimer: str = Field(
        default=PATENT_DISCLAIMER,
        description="Mandatory legal disclaimer"
    )
    external_search_performed: bool = Field(
        default=False,
        description="Explicit flag indicating whether external patent database search was conducted"
    )
    jurisdiction: Optional[str] = "United States"
    target_industry: Optional[str] = None
    paper_ids: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None


class PatentAnalysisRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Project title")
    idea_description: str = Field(..., min_length=10, description="Comprehensive description of the idea")
    problem_solved: str = Field(..., min_length=5, description="Problem being solved by the invention")
    technical_solution: str = Field(..., min_length=10, description="How the proposed technical solution works")
    differentiation_notes: Optional[str] = Field(default="", description="What makes the idea different")
    target_industry: Optional[str] = Field(default=None, description="Target industry or application domain")
    jurisdiction: Optional[str] = Field(default="United States", description="Target jurisdiction (US, India, etc.)")
    document_ids: List[str] = Field(default_factory=list, description="IDs of research papers to analyze against")


class PatentAnalysisSummaryItem(BaseModel):
    analysis_id: str
    title: str
    preliminary_assessment: str
    jurisdiction: Optional[str] = None
    num_papers: int = 0
    created_at: Optional[str] = None
