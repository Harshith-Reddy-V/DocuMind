# DocuMind Evaluation Suite

This directory contains the reproducible benchmark evaluation harness, academic PDF test documents, and query sets for **DocuMind Phase 1**.

---

## 1. Evaluation Dataset Overview

The dataset consists of **3 academic PDF benchmark documents** (3 pages each) and **30 evaluation queries** spanning in-document questions, unanswerable out-of-document questions, and multi-page synthesis questions:

1. **`paper_1_deep_learning.pdf`**:
   - Focus: Deep learning document visual representation (CNN architecture, AdamW optimizer, RVL-CDIP benchmark).
2. **`paper_2_quantum_computing.pdf`**:
   - Focus: Quantum search algorithms (Grover's algorithm, O(sqrt(N)) query complexity, superconducting transmons, decoherence limits).
3. **`paper_3_distributed_systems.pdf`**:
   - Focus: Distributed consensus (Raft protocol, 150-300ms election timeouts, failover latencies, CAP theorem CP trade-offs).

### Query Distribution:
- **15 In-Document Single-Page Questions**: Factually supported by a single specific page.
- **9 Out-of-Document Questions**: General or out-of-domain knowledge not present in the document (e.g. "Who invented CNN?", "What is the speed of light?"). Must trigger the **exact refusal sentence**:
  `"The answer could not be found in the uploaded document."`
- **6 Multi-Page Synthesis Questions**: Requires evidence spanning multiple distinct pages.

---

## 2. Evaluation Metrics

1. **Answer Correctness**: Percentage of in-document questions answered with correct factual content.
2. **Refusal Precision**: Fraction of refused queries that were genuinely out-of-document ($TP / (TP + FP)$).
3. **Refusal Recall**: Fraction of out-of-document queries successfully rejected ($TP / (TP + FN)$).
4. **Citation Correctness**: Percentage of answered queries whose page citations match the ground-truth document pages.
5. **Mean Ingestion Latency**: Mean time in seconds to validate, extract, chunk, embed, and index an academic paper.
6. **Mean Query Latency**: Mean time in milliseconds to retrieve, gate, and answer a question.

---

## 3. Measured Results (Empirical Benchmark)

The evaluation was executed on the 30-query academic benchmark with the following measured results:

| Configuration | Answer correctness | Refusal precision | Refusal recall | Citation correctness | Mean query latency |
|---|---:|---:|---:|---:|---:|
| **Full-document baseline** | 33.3% | 80.0% | 88.9% | 36.8% | 0.1 ms |
| **DocuMind RAG** | **38.1%** | **80.0%** | **88.9%** | **89.5%** | 9.3 ms |

### Key Findings:
- **Citation Precision**: DocuMind RAG achieved **89.5% citation correctness**, compared to **36.8%** for the baseline. The baseline either cites page 1 indiscriminately or fails to attribute factual claims to specific pages.
- **Evidence Gating**: The retrieval gate prevents generation when vector similarity falls below the threshold, protecting against hallucinated answers on irrelevant queries.

---

## 4. Parameter Sensitivity Sweep

Retrieval behavior was evaluated across different cosine similarity thresholds:

| Cosine Threshold | In-Doc Answer Accuracy | Out-of-Doc Refusal Recall | Analysis & Recommendation |
|---|---:|---:|---|
| **0.40** | 38.1% | 88.9% | Permissive: accepts borderline chunks, higher risk of noisy context. |
| **0.55 (Selected)** | **38.1%** | **88.9%** | **Optimal balance: maintains high recall while rejecting irrelevant content.** |
| **0.70** | 28.6% | 100.0% | Conservative: rejects some relevant paraphrased queries (false negatives). |

Selected Default Configuration:
- `SIMILARITY_THRESHOLD=0.55`
- `TOP_K=5`
- `CHUNK_SIZE=800` characters with `CHUNK_OVERLAP=150`

---

## 5. How to Run the Evaluation

From the workspace root or `evaluation/`:

```powershell
# 1. Regenerate dataset (if needed)
.\backend\.venv\Scripts\python.exe evaluation/dataset/generate_dataset.py

# 2. Run evaluation harness
.\backend\.venv\Scripts\python.exe evaluation/evaluate.py
```

Results are saved to `evaluation/evaluation_results.json`.
