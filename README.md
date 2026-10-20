# DocuMind

**DocuMind: A Gemini-Powered Grounded Question-Answering and Summarization Assistant for Academic Documents.**

DocuMind is an academic assistant designed for university students, researchers, and educators. It allows users to upload academic PDFs (research papers, textbooks, lecture notes), ask factual questions, inspect verifiable page-level source citations, and generate structured summaries and paper overviews.

DocuMind operates on a **fixed, deterministic Retrieval-Augmented Generation (RAG) pipeline**:

$$\text{PDF} \longrightarrow \text{Extraction / OCR} \longrightarrow \text{Chunking} \longrightarrow \text{Embeddings} \longrightarrow \text{Vector Store} \longrightarrow \text{Retrieval Gate} \longrightarrow \text{Grounded Answer} \longrightarrow \text{Citations}$$

> [!NOTE]
> DocuMind is strictly a grounded RAG assistant, **not an autonomous agent system**. It does not perform autonomous planning, arbitrary tool execution, or cross-session state changes.

---

## Key Features (Phase 1)

- 📄 **PDF Ingestion & Content Validation**: Validates PDF structure, header bytes (`%PDF-`), encryption status, and page counts.
- 👁️ **Automatic OCR Fallback**: PyMuPDF page-by-page text extraction with automatic 200 DPI multimodal vision OCR for scanned or image-only pages. OCR failure placeholders are **never indexed**.
- ✂️ **Page-Aware Chunking**: Paragraph and sentence-aware sliding window chunking with start and end page provenance.
- 🗄️ **ChromaDB Persistent Vectors**: Isolated per-document collections configured with **cosine space semantics** ($d = 1 - \cos\theta \implies \text{similarity} = 1 - d$).
- 💾 **SQLite Metadata Persistence**: SQLAlchemy-backed persistence for document statuses, processing stages, OCR flags, and warnings across restarts.
- 🛡️ **Evidence Gate & Strict Grounding**: Discards chunks below the cosine threshold (`0.55`). If no chunks pass, immediately returns the exact refusal sentence without calling the LLM generator.
- 🚫 **Exact Refusal Sentence**:
  `"The answer could not be found in the uploaded document."`
- 📌 **Traceable Citations**: Returns exact page numbers, text snippets, chunk IDs, and similarity scores.
- 📑 **Hierarchical Summarization**: Map-reduce summarization preventing token window saturation on long documents.
- 🔬 **Structured Paper Analysis**: Extracts title, authors, abstract, methodology, datasets, results, limitations, and future work.
- ⚡ **Asynchronous Background Processing**: Background ingestion with stage-by-stage status polling for frontend progress bars.
- 💡 **AI Patent Feasibility Analyzer**: Evaluates proposed project/invention ideas against academic prior art research papers. Assesses novelty signals, potential inventive steps, patentability concerns (subject matter eligibility under US 101 / Indian Patent Act Sec 3), engineering feasibility risks, research gaps, and actionable inventor next steps with page-level citations and mandatory legal disclaimers.
- 🔒 **Security & Reliability**: Rate limiting on expensive endpoints, filename collision prevention, directory traversal protection, and error sanitization.

---

## System Architecture

```
PDF Upload
   ↓
Validation Engine ── (magic bytes, encryption, size)
   ↓
Text Extraction (PyMuPDF) ── chars < 20? ──▶ Gemini Multimodal Vision OCR (200 DPI)
   ↓
Page-Aware Chunking (800 chars / 150 overlap)
   ↓
Batch Embeddings (Gemini text-embedding-004)
   ↓
Vector DB (ChromaDB with cosine metric) + SQLite Metadata Registry
   ↓
User Question ──▶ Embedding ──▶ Vector Search ──▶ Relevance Gate (threshold >= 0.55)
                                                         │
   ┌─────────────────────────────────────────────────────┘
   ↓ (no chunks pass threshold)                          ↓ (chunks pass)
"The answer could not be found in the uploaded document."   Gemini 2.5 Flash Grounded Generation (Pydantic JSON Schema)
(Generator never called)                                 ↓
                                                         Answer + Page Citations + Grounding Level
```

---

## Repository Structure

```
AI-Project/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entrypoint & lifespan
│   │   ├── config.py                # Centralized settings & environment loader
│   │   ├── database.py              # SQLAlchemy engine, session maker & init
│   │   ├── models/
│   │   │   ├── schemas.py           # Pydantic request & response models
│   │   │   └── database_models.py   # SQLAlchemy ORM DocumentModel
│   │   ├── routes/
│   │   │   ├── documents.py         # Upload, status, file, query, summarize, analysis
│   │   │   └── workspace.py         # Multi-document workspace queries
│   │   ├── services/
│   │   │   ├── pdf_service.py       # Validation & page text extraction
│   │   │   ├── ocr_service.py       # Multimodal OCR transcription
│   │   │   ├── chunking_service.py  # Page-aware paragraph/sentence chunker
│   │   │   ├── gemini_service.py    # Provider abstraction (Real & Mock)
│   │   │   ├── vectorstore_service.py # ChromaDB cosine space wrapper
│   │   │   ├── rag_service.py       # Retrieve -> Gate -> Generate flow
│   │   │   ├── ingestion_service.py # Pipeline orchestration & status stages
│   │   │   ├── summarization_service.py # Hierarchical map-reduce summarizer
│   │   │   ├── analysis_service.py  # Structured paper analysis & study guide
│   │   │   └── document_store.py    # SQLite CRUD operations
│   │   └── utils/
│   │       └── rate_limiter.py      # Sliding-window rate limiter
│   ├── tests/
│   │   ├── conftest.py              # Isolated temp db & mock provider fixtures
│   │   ├── test_pdf_service.py      # Validation, extraction, OCR tests
│   │   ├── test_chunking.py         # Sentence splitting & page tracking tests
│   │   ├── test_vectorstore.py      # Cosine metric & similarity tests
│   │   ├── test_rag.py              # Gate, refusals, citations, injection tests
│   │   ├── test_persistence.py      # Restart survival tests
│   │   ├── test_upload.py           # Collision, status, deletion tests
│   │   ├── test_summarization.py    # Hierarchical summary & analysis tests
│   │   └── test_security.py         # Rate limit & traversal tests
│   ├── smoke_test.py                # Live Gemini API smoke test script
│   ├── requirements.txt             # Pinned backend dependencies
│   ├── .env.example                 # Environment configuration template
│   └── pytest.ini
├── evaluation/
│   ├── dataset/
│   │   ├── generate_dataset.py      # Generates benchmark PDFs and queries
│   │   ├── eval_questions.json      # 30 benchmark queries
│   │   ├── paper_1_deep_learning.pdf
│   │   ├── paper_2_quantum_computing.pdf
│   │   └── paper_3_distributed_systems.pdf
│   ├── evaluate.py                  # Evaluation benchmark harness
│   ├── evaluation_results.json      # Measured benchmark results
│   └── README.md                    # Evaluation documentation
├── docs/
│   ├── architecture.md              # In-depth architectural design
│   ├── api.md                       # Complete API specification for frontend
│   └── evaluation.md                # Evaluation report & presentation guide
├── frontend/                        # React + Vite + TypeScript frontend (Phase 2)
├── pytest.ini
├── README.md
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Python 3.12 (recommended for Windows wheels compatibility)
- Node.js 18+ (for frontend, Phase 2)
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

---

### Backend Installation & Setup (Windows PowerShell)

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment using Python 3.12
py -3.12 -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install pinned dependencies
python -m pip install -r requirements.txt

# 5. Configure environment variables
Copy-Item .env.example .env
```

Open `backend/.env` and insert your Gemini API key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

---

### Running the Backend

From the `backend/` directory with virtual environment activated:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

---

## Running Automated Tests

The test suite runs **100% offline without requiring a real Gemini API key**, using an injectable deterministic mock provider.

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

All 26 automated unit and scenario tests will run and pass:
- PDF structure and OCR fallback tests (including Scenarios D & E)
- Similarity scoring and ChromaDB cosine space tests (Scenario G)
- Retrieval gate and exact refusal tests (Scenarios A, B, B2)
- Multi-page citation tests (Scenario C)
- Restart persistence tests (Scenario F)
- Prompt injection resistance tests (Scenario H)
- Filename collision and rate-limiting security tests

---

## Live Gemini API Smoke Test

When a valid `GEMINI_API_KEY` is configured in `backend/.env`, you can verify live API connectivity across generation, embeddings, and vision OCR:

```powershell
.\.venv\Scripts\python.exe smoke_test.py
```

If the key is unset, the script cleanly reports that live tests were skipped without breaking builds.

---

## Running the Evaluation Benchmark

Run the reproducible benchmark harness to measure ingestion latency, query latency, refusal precision/recall, and citation accuracy:

```powershell
# From workspace root:
.\backend\.venv\Scripts\python.exe evaluation/evaluate.py
```

### Measured Benchmark Results Table

| Configuration | Answer correctness | Refusal precision | Refusal recall | Citation correctness | Mean query latency |
|---|---:|---:|---:|---:|---:|
| **Full-document baseline** | 33.3% | 80.0% | 88.9% | 36.8% | 0.1 ms |
| **DocuMind RAG** | **38.1%** | **80.0%** | **88.9%** | **89.5%** | **9.3 ms** |

---

## Configuration Variables (`backend/.env`)

| Variable | Description | Default |
|---|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key | `""` |
| `GEMINI_GENERATION_MODEL` | Gemini model for grounded generation | `gemini-2.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Embedding model for vector indexing | `text-embedding-004` |
| `TOP_K` | Number of chunks retrieved per question | `5` |
| `SIMILARITY_THRESHOLD` | Cosine similarity cutoff for evidence gate | `0.55` |
| `CHUNK_SIZE` | Target chunk size (in characters) | `800` |
| `CHUNK_OVERLAP` | Overlap between consecutive chunks | `150` |
| `UPLOAD_DIR` | Directory for uploaded PDF storage | `./data/uploads` |
| `VECTOR_DB_DIR` | Directory for ChromaDB vector storage | `./data/chroma` |
| `DATABASE_URL` | SQLite connection URL | `sqlite:///./data/documind.db` |
| `MAX_FILE_SIZE_MB` | Maximum allowed upload size | `20` |
| `ALLOWED_ORIGINS` | Permitted CORS frontend origins | `http://localhost:5173` |
| `RATE_LIMIT_PER_MINUTE` | Maximum requests per minute per IP | `30` |

---

## Frontend Integration Guide (For Teammate - Phase 2)

The backend provides a typed REST API for the React frontend:

1. **Upload & Status Polling**:
   - Call `POST /api/documents/upload` with FormData (`file`).
   - Immediately receive `{"document_id": "...", "status": "processing"}`.
   - Poll `GET /api/documents/{id}/status` every 1.5 seconds. Display the `progress_percent` and `current_stage` in your progress bar.
   - When `status === "ready"`, redirect to document chat.
2. **Grounded Q&A**:
   - Call `POST /api/documents/{id}/query` with `{"question": "...", "mode": "document", "history": []}`.
   - Display `response.answer`.
   - Render `response.sources` as clickable citations displaying `page`, `chunk_id`, and `score`.
3. **Summaries & Analysis**:
   - `POST /api/documents/{id}/summarize` for short and detailed summaries.
   - `POST /api/documents/{id}/analysis` for structured paper overview.
   - `POST /api/documents/{id}/study` for interactive MCQs and flashcards.
4. **PDF Viewer**:
   - Render the PDF using an `<iframe>` pointing to `GET /api/documents/{id}/file`.
5. **Patent Feasibility Analyzer**:
   - `POST /api/patent/analyze`: Submits project idea fields and document IDs, returning `PatentFeasibilityReport`.
   - `GET /api/patent/analyses`: Lists saved patent evaluations.
   - `GET /api/patent/analyses/{id}`: Retrieves full saved evaluation.
   - `DELETE /api/patent/analyses/{id}`: Deletes saved evaluation.

See [`docs/api.md`](docs/api.md) for full TypeScript interfaces and request/response examples.

---

## Known Limitations & Honest Grounding Claims

- **Honest Grounding**: RAG and the retrieval gate substantially mitigate hallucinations, but no LLM architecture mathematically guarantees zero hallucinations.
- **Complex Diagrams**: Mathematical formula extraction and intricate vector graphic diagram parsing rely on text extraction and multimodal OCR; handwritten annotations may vary in OCR quality.
- **Single-User Workspace**: Phase 1 implements workspace persistence without multi-user authentication. Multi-user accounts can be layered in future phases.
