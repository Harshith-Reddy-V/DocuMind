import type {
  DocumentInfo,
  QueryResponse,
  SummarizeResponse,
  PatentAnalysisRequest,
  PatentFeasibilityReport,
  PatentAnalysisSummaryItem,
} from "../types";

const configuredBase = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? "http://localhost:8000" : "")
).trim();

const API_BASE = configuredBase.replace(/\/+$/, "");

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = "Something went wrong.";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse errors, use default message
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<DocumentInfo>(res);
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_BASE}/api/documents`);
  return handleResponse<DocumentInfo[]>(res);
}

export async function queryDocument(documentId: string, question: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return handleResponse<QueryResponse>(res);
}

export async function summarizeDocument(documentId: string): Promise<SummarizeResponse> {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}/summarize`, {
    method: "POST",
  });
  return handleResponse<SummarizeResponse>(res);
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}`, {
    method: "DELETE",
  });
  await handleResponse(res);
}

export async function analyzePatentFeasibility(
  request: PatentAnalysisRequest
): Promise<PatentFeasibilityReport> {
  const res = await fetch(`${API_BASE}/api/patent/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  return handleResponse<PatentFeasibilityReport>(res);
}

export async function listPatentAnalyses(): Promise<PatentAnalysisSummaryItem[]> {
  const res = await fetch(`${API_BASE}/api/patent/analyses`);
  return handleResponse<PatentAnalysisSummaryItem[]>(res);
}

export async function getPatentAnalysis(
  analysisId: string
): Promise<PatentFeasibilityReport> {
  const res = await fetch(`${API_BASE}/api/patent/analyses/${analysisId}`);
  return handleResponse<PatentFeasibilityReport>(res);
}

export async function deletePatentAnalysis(analysisId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/patent/analyses/${analysisId}`, {
    method: "DELETE",
  });
  await handleResponse(res);
}
