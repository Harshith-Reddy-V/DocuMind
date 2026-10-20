# DocuMind API Specification (Frontend Integration Guide)

This document provides the complete API specification for the React, Vite, TypeScript, and Tailwind CSS frontend developer (Phase 2).

- **Base URL:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **Error Response Shape:**
  ```json
  {
    "detail": "Error explanation message",
    "code": "OPTIONAL_ERROR_CODE"
  }
  ```

---

## 1. Endpoints

### 1.1 Health Check
**`GET /api/health`**

Returns backend health status and indicates whether the Gemini API key is configured.

**Response (200 OK):**
```json
{
  "status": "ok",
  "gemini_key_configured": true,
  "generation_model": "gemini-2.5-flash",
  "embedding_model": "text-embedding-004"
}
```

---

### 1.2 Upload Document
**`POST /api/documents/upload`**

Accepts a multipart PDF upload, validates the file structure and size, stores it safely under a unique document ID, and begins background ingestion.

- **Content-Type:** `multipart/form-data`
- **Body:** `file: File` (PDF file, max 20 MB)

**Response (200 OK):**
```json
{
  "document_id": "a1b2c3d4e5f6",
  "filename": "deep_learning_paper.pdf",
  "status": "processing",
  "num_pages": 0,
  "num_chunks": 0,
  "used_ocr": false,
  "warnings": []
}
```

> **Frontend Integration Note:** After receiving this response, poll `GET /api/documents/{id}/status` every 1–2 seconds until `status` becomes `"ready"` or `"failed"`.

---

### 1.3 Check Processing Status (Polling)
**`GET /api/documents/{id}/status`**

Returns stage-by-stage ingestion progress, current stage name, and any warnings.

**Stages:**
- `validating`: Checking PDF structure and encryption.
- `extracting`: Extracting text page-by-page with PyMuPDF.
- `ocr`: Running multimodal vision transcription on image/scanned pages.
- `chunking`: Splitting into paragraph/sentence chunks.
- `embedding`: Generating vector embeddings via Gemini.
- `indexing`: Storing vectors in ChromaDB.
- `ready`: Document is ready for Q&A and summarization.
- `failed`: Ingestion failed; check `error_message`.

**Response (200 OK):**
```json
{
  "document_id": "a1b2c3d4e5f6",
  "filename": "deep_learning_paper.pdf",
  "status": "processing",
  "current_stage": "embedding",
  "progress_percent": 75,
  "num_pages": 12,
  "num_chunks": 38,
  "used_ocr": true,
  "warnings": [],
  "error_message": null
}
```

---

### 1.4 List Documents
**`GET /api/documents`**

Returns all documents currently persisted in the workspace.

**Response (200 OK):**
```json
[
  {
    "document_id": "a1b2c3d4e5f6",
    "filename": "deep_learning_paper.pdf",
    "num_pages": 12,
    "num_chunks": 38,
    "status": "ready",
    "used_ocr": true,
    "created_at": "2026-10-18T05:00:00Z"
  }
]
```

---

### 1.5 Get Document Metadata
**`GET /api/documents/{id}`**

Returns metadata for a single document.

**Response (200 OK):**
```json
{
  "document_id": "a1b2c3d4e5f6",
  "filename": "deep_learning_paper.pdf",
  "num_pages": 12,
  "num_chunks": 38,
  "status": "ready",
  "used_ocr": true,
  "current_stage": "ready",
  "progress_percent": 100,
  "warnings": [],
  "error_message": null,
  "created_at": "2026-10-18T05:00:00Z"
}
```

---

### 1.6 Download / View Document File
**`GET /api/documents/{id}/file`**

Serves the original uploaded PDF. Can be passed directly into an `<iframe>` or PDF viewer component.

**Response (200 OK):**
- Headers: `Content-Type: application/pdf`
- Body: Binary PDF stream

---

### 1.7 Ask Grounded Question
**`POST /api/documents/{id}/query`**

Submits a question grounded strictly in the document.

**Request Body:**
```json
{
  "question": "What model does the proposed system use?",
  "mode": "document",
  "history": [
    {"role": "user", "content": "Tell me about the paper."},
    {"role": "assistant", "content": "The paper presents VisionDocNet."}
  ],
  "top_k": 5
}
```

**Response (200 OK - Answer Found):**
```json
{
  "answer": "The proposed system uses a CNN model featuring depthwise separable convolutions.",
  "grounded": true,
  "grounding_level": "strongly_supported",
  "sources": [
    {
      "page": 2,
      "start_page": 2,
      "end_page": 2,
      "text": "The proposed system uses a CNN model featuring depthwise separable convolutions...",
      "chunk_id": "chunk_0003",
      "score": 0.8421,
      "document_id": "a1b2c3d4e5f6"
    }
  ]
}
```

**Response (200 OK - Refusal / Unanswerable):**
```json
{
  "answer": "The answer could not be found in the uploaded document.",
  "grounded": false,
  "grounding_level": "insufficient_evidence",
  "sources": []
}
```

---

### 1.8 Summarize Document
**`POST /api/documents/{id}/summarize`**

Generates hierarchical short and detailed summaries.

**Response (200 OK):**
```json
{
  "short_summary": "This paper presents VisionDocNet, a 12-layer CNN for academic document classification.",
  "detailed_summary": "1. Introduction:\nDocument layout understanding requires visual modeling...\n\n2. Methodology:\nUses depthwise separable convolutions with AdamW optimizer...\n\n3. Results:\nAchieves 92.4% test accuracy on RVL-CDIP.",
  "section_summaries": [
    {
      "heading": "Section 1",
      "content": "Overview of visual document classification challenges."
    }
  ]
}
```

---

### 1.9 Structured Paper Analysis
**`POST /api/documents/{id}/analysis`**

Extracts research paper attributes into structured fields.

**Response (200 OK):**
```json
{
  "title": "VisionDocNet: Deep Learning for Document Classification",
  "authors": ["Author One", "Author Two"],
  "abstract": "We introduce a convolutional neural network model...",
  "keywords": ["CNN", "Document Classification", "Deep Learning"],
  "methodology": "Depthwise separable convolutions optimized with AdamW",
  "dataset": "RVL-CDIP (400,000 images)",
  "results": "92.4% top-1 accuracy",
  "limitations": "High memory consumption during 200 DPI batch inference",
  "future_work": "Quantized inference on edge devices",
  "references": ["ResNet-50", "AdamW Optimizer"]
}
```

---

### 1.10 Study Tools (MCQs, Viva Questions, Flashcards)
**`POST /api/documents/{id}/study`**

Generates revision flashcards, exam questions, and viva preparation items.

**Response (200 OK):**
```json
{
  "mcqs": [
    {
      "question": "What optimizer is used during training?",
      "options": ["SGD", "AdamW", "RMSProp", "Adagrad"],
      "correct_answer": "AdamW",
      "explanation": "Described in Methodology Section."
    }
  ],
  "viva_questions": [
    {
      "question": "Explain how depthwise separable convolutions reduce parameter complexity.",
      "suggested_answer": "By splitting convolution into spatial and depthwise stages."
    }
  ],
  "flashcards": [
    {
      "front": "Cosine Annealing",
      "back": "Learning rate scheduling strategy that decreases learning rate following a cosine curve."
    }
  ],
  "key_notes": [
    "Operates on 224x224 grayscale and RGB page images.",
    "Trained across 50 epochs."
  ]
}
```

---

### 1.11 Multi-Document Workspace Query
**`POST /api/workspace/query`**

Queries across multiple documents in the workspace.

**Request Body:**
```json
{
  "question": "Compare the evaluation datasets across the papers.",
  "document_ids": ["doc_1", "doc_2"],
  "top_k": 5
}
```

---

### 1.12 Delete Document
**`DELETE /api/documents/{id}`**

Deletes the document's SQLite record, stored PDF, and ChromaDB vector collection.

**Response (200 OK):**
```json
{
  "status": "deleted"
}
```

---

## 2. TypeScript Types for React Frontend

You can paste this directly into `frontend/src/types/index.ts`:

```typescript
export interface DocumentInfo {
  document_id: string;
  filename: string;
  num_pages: number;
  num_chunks: number;
  status: "processing" | "ready" | "failed";
  used_ocr?: boolean;
  current_stage?: string;
  progress_percent?: number;
  warnings?: string[];
  error_message?: string | null;
  created_at?: string;
}

export interface DocumentStatusResponse {
  document_id: string;
  filename: string;
  status: "processing" | "ready" | "failed";
  current_stage: string;
  progress_percent: number;
  num_pages: number;
  num_chunks: number;
  used_ocr: boolean;
  warnings: string[];
  error_message?: string | null;
}

export interface SourceReference {
  page: number;
  text: string;
  chunk_id: string;
  score: number;
  start_page?: number;
  end_page?: number;
  document_id?: string;
}

export interface QueryResponse {
  answer: string;
  grounded: boolean;
  grounding_level: "strongly_supported" | "partially_supported" | "insufficient_evidence";
  sources: SourceReference[];
}

export interface SummarizeResponse {
  short_summary: string;
  detailed_summary: string;
  section_summaries?: { heading: string; content: string }[];
}

export interface PaperAnalysisResponse {
  title: string;
  authors: string[];
  abstract: string;
  keywords: string[];
  methodology: string;
  dataset: string;
  results: string;
  limitations: string;
  future_work: string;
  references: string[];
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
```

---

## 2. Patent Feasibility Analyzer Endpoints

### 2.1 Analyze Patent Potential
**`POST /api/patent/analyze`**

Evaluates a proposed invention or project idea against one or more uploaded/selected research papers.
Rate limited (30 requests/minute).

- **Headers:** `Content-Type: application/json`
- **Body:** `PatentAnalysisRequest`
  ```json
  {
    "title": "Quantum-Assisted Neuromorphic Vision Sensor",
    "idea_description": "A novel hybrid quantum-neuromorphic sensor architecture for edge vision processing.",
    "problem_solved": "High energy consumption and latency in conventional CMOS vision processing.",
    "technical_solution": "Integrate superconducting quantum interference devices with asynchronous spike timing circuits.",
    "differentiation_notes": "Eliminates ADC stages completely using direct flux-to-spike modulation.",
    "target_industry": "Autonomous Robotics & Aerospace",
    "jurisdiction": "United States",
    "document_ids": ["doc_12345678"]
  }
  ```

**Response (200 OK):** `PatentFeasibilityReport`
```json
{
  "analysis_id": "8f3b21c4e90a",
  "title": "Quantum-Assisted Neuromorphic Vision Sensor",
  "executive_summary": "The proposed idea exhibits distinguishing technical features...",
  "preliminary_assessment": "Potentially worth further investigation",
  "preliminary_assessment_explanation": "While the supplied papers establish foundational principles...",
  "idea_decomposition": [
    "Superconducting quantum interference detection",
    "Asynchronous spike timing circuit"
  ],
  "paper_comparisons": [
    {
      "document_id": "doc_12345678",
      "paper_title": "baseline_vision.pdf",
      "relevant_approach": "Discloses baseline CMOS edge architectures.",
      "overlapping_features": ["Vision sensor edge deployment"],
      "differences": ["Lacks direct flux-to-spike modulation"],
      "strongest_evidence": "Conventional sensors require ADC conversion...",
      "page_references": [1, 3],
      "remaining_uncertainties": "Cryogenic cooling requirements."
    }
  ],
  "potentially_differentiating_features": [
    "Direct flux-to-spike modulation without intermediate ADC"
  ],
  "prior_art_findings": [
    {
      "finding": "Paper discloses baseline CMOS sensors.",
      "explanation": "Establishes standard ADC pipeline.",
      "supporting_evidence": "Conventional architectures rely on ADCs...",
      "source_paper_title": "baseline_vision.pdf",
      "page_number": 1,
      "confidence": "high",
      "is_direct_support": true
    }
  ],
  "technical_feasibility_risks": [
    "Integration hurdles with standard CMOS foundry processes"
  ],
  "research_gaps": [
    "Real-world thermal performance at room temperatures"
  ],
  "patentability_concerns": {
    "novelty": "Prima facie distinguishable from supplied papers",
    "inventive_step": "Non-obvious technical effect must be verified",
    "subject_matter_eligibility": "Clear statutory physical apparatus under 35 U.S.C. 101"
  },
  "suggested_next_steps": [
    "Fabricate proof-of-concept prototype",
    "Conduct exhaustive commercial patent search (USPTO, EPO)"
  ],
  "disclaimer": "This report is an AI-assisted preliminary research tool...",
  "external_search_performed": false,
  "jurisdiction": "United States",
  "target_industry": "Autonomous Robotics & Aerospace",
  "paper_ids": ["doc_12345678"],
  "created_at": "2026-10-21T00:00:00Z"
}
```

---

### 2.2 List Saved Patent Evaluations
**`GET /api/patent/analyses`**

Returns summary cards of all saved patent evaluations ordered newest first.

**Response (200 OK):**
```json
[
  {
    "analysis_id": "8f3b21c4e90a",
    "title": "Quantum-Assisted Neuromorphic Vision Sensor",
    "preliminary_assessment": "Potentially worth further investigation",
    "jurisdiction": "United States",
    "num_papers": 1,
    "created_at": "2026-10-21T00:00:00Z"
  }
]
```

---

### 2.3 Get Saved Patent Evaluation
**`GET /api/patent/analyses/{analysis_id}`**

Returns the complete structured `PatentFeasibilityReport` for the given ID.
Returns `404` if not found.

---

### 2.4 Delete Saved Patent Evaluation
**`DELETE /api/patent/analyses/{analysis_id}`**

Deletes the saved evaluation record from SQLite.
Returns `{"status": "deleted", "analysis_id": "8f3b21c4e90a"}`.

