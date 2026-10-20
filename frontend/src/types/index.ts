export interface DocumentInfo {
  document_id: string;
  filename: string;
  num_pages: number;
  num_chunks: number;
  used_ocr?: boolean;
  status: string;
}

export interface SourceReference {
  page: number;
  text: string;
  chunk_id: string;
  score: number;
}

export interface QueryResponse {
  answer: string;
  grounded: boolean;
  sources: SourceReference[];
}

export interface SummarizeResponse {
  short_summary: string;
  detailed_summary: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceReference[];
  grounded?: boolean;
  isError?: boolean;
}

export interface FindingEvidence {
  finding: string;
  explanation?: string;
  supporting_evidence: string;
  source_paper_title: string;
  page_number?: number | null;
  confidence: "high" | "medium" | "low";
  is_direct_support: boolean;
}

export interface PaperComparison {
  document_id: string;
  paper_title: string;
  relevant_approach: string;
  overlapping_features: string[];
  differences: string[];
  strongest_evidence: string;
  page_references: number[];
  remaining_uncertainties?: string;
}

export interface PatentFeasibilityReport {
  analysis_id?: string;
  title: string;
  executive_summary: string;
  preliminary_assessment:
    | "Potentially worth further investigation"
    | "Significant overlap found in supplied papers"
    | "Insufficient evidence to assess";
  preliminary_assessment_explanation: string;
  idea_decomposition: string[];
  paper_comparisons: PaperComparison[];
  potentially_differentiating_features: string[];
  prior_art_findings: FindingEvidence[];
  technical_feasibility_risks: string[];
  research_gaps: string[];
  patentability_concerns: Record<string, string>;
  suggested_next_steps: string[];
  disclaimer: string;
  external_search_performed: boolean;
  jurisdiction?: string;
  target_industry?: string;
  paper_ids: string[];
  created_at?: string;
}

export interface PatentAnalysisRequest {
  title: string;
  idea_description: string;
  problem_solved: string;
  technical_solution: string;
  differentiation_notes?: string;
  target_industry?: string;
  jurisdiction?: string;
  document_ids: string[];
}

export interface PatentAnalysisSummaryItem {
  analysis_id: string;
  title: string;
  preliminary_assessment: string;
  jurisdiction?: string;
  num_papers: number;
  created_at?: string;
}
