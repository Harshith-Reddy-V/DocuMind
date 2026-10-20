# DocuMind Phase 1 Evaluation & Benchmark Report

This document reports the empirical evaluation results for **DocuMind Phase 1**. All metrics were produced by executing the reproducible evaluation harness (`evaluation/evaluate.py`) against synthetic benchmark academic documents and questions.

---

## 1. Evaluation Methodology

### 1.1 Dataset Composition
- **Benchmark Corpus**: 3 distinct 3-page academic papers (`paper_1_deep_learning.pdf`, `paper_2_quantum_computing.pdf`, `paper_3_distributed_systems.pdf`).
- **Query Set**: 30 total questions:
  - 15 single-page factual questions with ground-truth answers.
  - 9 out-of-document unanswerable questions (which must trigger the exact refusal sentence).
  - 6 multi-page synthesis questions requiring evidence spanning multiple pages.

### 1.2 Evaluation Metrics
- **Answer Correctness**: Semantic/keyword containment against ground-truth answer snippets.
- **Refusal Precision**: $TP / (TP + FP)$ where $TP$ is out-of-document queries refused, and $FP$ is in-document queries erroneously refused.
- **Refusal Recall**: $TP / (TP + FN)$ where $FN$ is out-of-document queries erroneously answered.
- **Citation Correctness**: Overlap between retrieved chunk source page and ground-truth evidence page.
- **Mean Query Latency**: Time in milliseconds from query receipt to response return.
- **Mean Ingestion Latency**: Time in seconds to validate, extract, chunk, embed, and index a document.

---

## 2. Benchmark Comparison Table

The table below compares the **Full-Document Baseline** (sending entire PDF text to the LLM without retrieval gating) against the **DocuMind RAG** pipeline:

| Configuration | Answer correctness | Refusal precision | Refusal recall | Citation correctness | Mean query latency |
|---|---:|---:|---:|---:|---:|
| **Full-document baseline** | 33.3% | 80.0% | 88.9% | 36.8% | 0.1 ms |
| **DocuMind RAG** | **38.1%** | **80.0%** | **88.9%** | **89.5%** | **9.3 ms** |

*(Tested on 30 evaluation queries across 3 academic papers).*

---

## 3. Analysis & Key Takeaways

### 3.1 Superior Citation Accuracy (89.5% vs 36.8%)
In the Full-Document Baseline, the language model receives the entire document text in one prompt. Because standard generation outputs unstructured text without per-passage vector provenance, it cannot accurately attribute specific factual claims to the exact page where they originated. DocuMind RAG maintains **89.5% citation correctness** by preserving page metadata throughout extraction, chunking, and vector retrieval.

### 3.2 Evidence Gating & Hallucination Mitigation
The retrieval gate enforces a strict cosine similarity threshold (`SIMILARITY_THRESHOLD = 0.55`). When an out-of-document query (such as "Who invented the CNN?" or "What is the speed of light?") fails to clear the threshold, the generation model is **never invoked**, and the exact refusal sentence is returned immediately:
`"The answer could not be found in the uploaded document."`

### 3.3 Parameter Tuning Analysis
Retrieval behavior was evaluated across candidate similarity thresholds:
- **Threshold 0.40**: Permissive. Achieved 38.1% accuracy and 88.9% refusal recall. Allowed some borderline noisy chunks into generation context.
- **Threshold 0.55 (Selected Default)**: Balanced. Preserves 38.1% accuracy while filtering irrelevant queries.
- **Threshold 0.70**: Conservative. Refusal recall increased to 100.0%, but in-document accuracy dropped to 28.6% due to false-negative rejections of valid paraphrased questions.

---

## 4. Ingestion Performance
- Mean ingestion latency across the benchmark corpus was **0.281 seconds** for 3-page academic documents.
- Asynchronous background processing ensures the upload API returns a document ID and `processing` status in `< 50 ms`, allowing the frontend to poll progress without blocking.
