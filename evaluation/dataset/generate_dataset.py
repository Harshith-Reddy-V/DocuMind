"""
Generates the benchmark evaluation academic PDFs and evaluation question dataset.
"""
import os
import json
import pymupdf

DATASET_DIR = os.path.dirname(os.path.abspath(__file__))

DOCUMENTS = {
    "paper_1_deep_learning.pdf": [
        (
            "DocuMind Academic Benchmark: Deep Learning for Vision\n\n"
            "Abstract:\n"
            "We introduce a convolutional neural network (CNN) model for visual document classification. "
            "Our model, dubbed VisionDocNet, uses 12 residual layers to extract invariant visual features. "
            "The model operates on 224x224 grayscale and RGB page images.\n\n"
            "1. Introduction:\n"
            "Academic document understanding requires capturing both typographical layout and visual structure. "
            "Traditional bag-of-words approaches fail to capture spatial hierarchies."
        ),
        (
            "2. Methodology and Architecture:\n"
            "The proposed system uses a CNN model featuring depthwise separable convolutions to reduce parameter count. "
            "Optimization is performed using the AdamW optimizer with an initial learning rate of 0.001. "
            "A cosine annealing learning rate scheduler is deployed across 50 training epochs. "
            "Batch normalization is applied after each convolutional block to stabilize gradient flows."
        ),
        (
            "3. Experiments and Results:\n"
            "We evaluated VisionDocNet on the RVL-CDIP benchmark dataset, comprising 400,000 document images. "
            "The proposed system achieved a top-1 test accuracy of 92.4%, outperforming standard ResNet-50 by 2.1%. "
            "Limitations include high memory consumption during 200 DPI batch inference. "
            "Future work will explore quantized inference on edge hardware."
        )
    ],
    "paper_2_quantum_computing.pdf": [
        (
            "DocuMind Academic Benchmark: Quantum Search Algorithms\n\n"
            "Abstract:\n"
            "Quantum computation exploits superposition and entanglement to solve unstructured search problems. "
            "We review Grover's algorithm and quadratic speedup in database search queries.\n\n"
            "1. Foundational Principles:\n"
            "A qubit resides in a state |psi> = alpha|0> + beta|1>, where |alpha|^2 + |beta|^2 = 1. "
            "Superposition allows 2^n simultaneous computational states for an n-qubit register."
        ),
        (
            "2. Grover's Algorithm Analysis:\n"
            "Grover's algorithm provides quadratic speedup for searching an unsorted database of N items. "
            "While classical search requires O(N) evaluations, Grover's search requires O(sqrt(N)) oracle queries. "
            "The algorithm iteratively applies an oracle reflection followed by a diffusion operator about the mean."
        ),
        (
            "3. Physical Implementations and Fault Tolerance:\n"
            "Physical realization of Grover's search was demonstrated using superconducting transmon qubits. "
            "Experimental fidelity reached 87.3% on a 5-qubit testbed. "
            "Decoherence times T1 and T2 remain the primary limiting factors for scale. "
            "Surface code error correction requires a physical-to-logical qubit ratio exceeding 1000:1."
        )
    ],
    "paper_3_distributed_systems.pdf": [
        (
            "DocuMind Academic Benchmark: Distributed Consensus\n\n"
            "Abstract:\n"
            "Fault-tolerant distributed state machine replication relies on consensus protocols. "
            "We evaluate the Raft consensus algorithm under network partition scenarios.\n\n"
            "1. System Model and Assumptions:\n"
            "We assume a partially synchronous network model where messages may experience arbitrary bounded delays. "
            "Node failures are assumed to follow the fail-stop model without Byzantine behavior."
        ),
        (
            "2. Raft Consensus Protocol:\n"
            "Raft organizes consensus through leader election, log replication, and safety invariants. "
            "Nodes exist in one of three states: Follower, Candidate, or Leader. "
            "Elections are governed by randomized election timeouts between 150ms and 300ms to prevent split votes."
        ),
        (
            "3. Performance and CAP Trade-offs:\n"
            "Under network partitions, Raft prioritizes consistency over availability (CP system under CAP theorem). "
            "In our 5-node cluster, leader failover completed in an average of 210ms. "
            "Throughput saturated at 45,000 replicated transactions per second with SSD-backed Write-Ahead Logging. "
            "Future work will evaluate multi-raft partitioning across geo-distributed regions."
        )
    ]
}

QUESTIONS = [
    # Paper 1 Questions (10 total: 5 in-doc, 3 out-of-doc, 2 multi-page)
    {"doc": "paper_1_deep_learning.pdf", "question": "What model does the system use?", "type": "in_doc", "expected_answer": "CNN model", "expected_pages": [2]},
    {"doc": "paper_1_deep_learning.pdf", "question": "What learning rate and optimizer are used?", "type": "in_doc", "expected_answer": "AdamW optimizer with an initial learning rate of 0.001", "expected_pages": [2]},
    {"doc": "paper_1_deep_learning.pdf", "question": "What dataset was used for evaluation?", "type": "in_doc", "expected_answer": "RVL-CDIP benchmark dataset", "expected_pages": [3]},
    {"doc": "paper_1_deep_learning.pdf", "question": "What accuracy did VisionDocNet achieve?", "type": "in_doc", "expected_answer": "92.4%", "expected_pages": [3]},
    {"doc": "paper_1_deep_learning.pdf", "question": "How many residual layers does VisionDocNet use?", "type": "in_doc", "expected_answer": "12 residual layers", "expected_pages": [1]},
    {"doc": "paper_1_deep_learning.pdf", "question": "Who invented the convolutional neural network?", "type": "out_of_doc", "expected_answer": None, "expected_pages": []},
    {"doc": "paper_1_deep_learning.pdf", "question": "What is the capital of France?", "type": "out_of_doc", "expected_answer": None, "expected_pages": []},
    {"doc": "paper_1_deep_learning.pdf", "question": "How does gradient boosting differ from random forests?", "type": "out_of_doc", "expected_answer": None, "expected_pages": []},
    {"doc": "paper_1_deep_learning.pdf", "question": "What image resolution does the model process and what accuracy does it achieve?", "type": "multi_page", "expected_answer": "224x224 and 92.4%", "expected_pages": [1, 3]},
    {"doc": "paper_1_deep_learning.pdf", "question": "What architecture is proposed and what are its inference limitations?", "type": "multi_page", "expected_answer": "CNN and high memory consumption", "expected_pages": [1, 2, 3]},

    # Paper 2 Questions (10 total: 5 in-doc, 3 out-of-doc, 2 multi-page)
    {"doc": "paper_2_quantum_computing.pdf", "question": "What is the query complexity of Grover's search algorithm?", "type": "in_doc", "expected_answer": "O(sqrt(N))", "expected_pages": [2]},
    {"doc": "paper_2_quantum_computing.pdf", "question": "What physical qubit technology was used in the experiments?", "type": "in_doc", "expected_answer": "superconducting transmon qubits", "expected_pages": [3]},
    {"doc": "paper_2_quantum_computing.pdf", "question": "What experimental fidelity was reached on the 5-qubit testbed?", "type": "in_doc", "expected_answer": "87.3%", "expected_pages": [3]},
    {"doc": "paper_2_quantum_computing.pdf", "question": "What physical-to-logical qubit ratio is required for surface codes?", "type": "in_doc", "expected_answer": "exceeding 1000:1", "expected_pages": [3]},
    {"doc": "paper_2_quantum_computing.pdf", "question": "What mathematical expression defines a single qubit state?", "type": "in_doc", "expected_answer": "|psi> = alpha|0> + beta|1>", "expected_pages": [1]},
    {"doc": "paper_2_quantum_computing.pdf", "question": "How do you build a nuclear fusion reactor?", "type": "out_of_doc", "expected_answer": None, "expected_pages": []},
    {"doc": "paper_2_quantum_computing.pdf", "question": "What is the population of Tokyo?", "type": "out_of_doc", "expected_answer": None, "expected_pages": []},
    {"doc": "paper_2_quantum_computing.pdf", "question": "Who was the first president of the United States?", "type": "out_of_doc", "expected_answer": None, "expected_pages": []},
    {"doc": "paper_2_quantum_computing.pdf", "question": "How does superposition relate to Grover's search speedup?", "type": "multi_page", "expected_answer": "superposition and quadratic speedup", "expected_pages": [1, 2]},
    {"doc": "paper_2_quantum_computing.pdf", "question": "What physical system was used and what are its limiting factors?", "type": "multi_page", "expected_answer": "superconducting transmon and decoherence times T1 and T2", "expected_pages": [2, 3]},

    # Paper 3 Questions (10 total: 5 in-doc, 3 out-of-doc, 2 multi-page)
    {"doc": "paper_3_distributed_systems.pdf", "question": "What are the three node states in the Raft consensus algorithm?", "type": "in_doc", "expected_answer": "Follower, Candidate, or Leader", "expected_pages": [2]},
    {"doc": "paper_3_distributed_systems.pdf", "question": "What election timeout range is used in Raft to avoid split votes?", "type": "in_doc", "expected_answer": "150ms and 300ms", "expected_pages": [2]},
    {"doc": "paper_3_distributed_systems.pdf", "question": "What average failover latency was observed in the 5-node cluster?", "type": "in_doc", "expected_answer": "210ms", "expected_pages": [3]},
    {"doc": "paper_3_distributed_systems.pdf", "question": "What throughput was achieved with SSD-backed logging?", "type": "in_doc", "expected_answer": "45,000 replicated transactions per second", "expected_pages": [3]},
    {"doc": "paper_3_distributed_systems.pdf", "question": "What failure model is assumed in the system?", "type": "in_doc", "expected_answer": "fail-stop model", "expected_pages": [1]},
    {"doc": "paper_3_distributed_systems.pdf", "question": "How do you train a generative adversarial network?", "type": "out_of_doc", "expected_answer": None, "expected_pages": []},
    {"doc": "paper_3_distributed_systems.pdf", "question": "What is the speed of light in vacuum?", "type": "out_of_doc", "expected_answer": None, "expected_pages": []},
    {"doc": "paper_3_distributed_systems.pdf", "question": "Who wrote the play Hamlet?", "type": "out_of_doc", "expected_answer": None, "expected_pages": []},
    {"doc": "paper_3_distributed_systems.pdf", "question": "Under the assumed network model, how does Raft handle CAP trade-offs?", "type": "multi_page", "expected_answer": "partially synchronous and consistency over availability (CP)", "expected_pages": [1, 3]},
    {"doc": "paper_3_distributed_systems.pdf", "question": "What election mechanism does Raft use and what failover speed was achieved?", "type": "multi_page", "expected_answer": "randomized election timeouts and 210ms", "expected_pages": [2, 3]}
]


def build_evaluation_dataset():
    os.makedirs(DATASET_DIR, exist_ok=True)

    # 1. Generate PDFs
    for filename, pages in DOCUMENTS.items():
        pdf_path = os.path.join(DATASET_DIR, filename)
        doc = pymupdf.open()
        for page_text in pages:
            page = doc.new_page()
            page.insert_text((50, 72), page_text, fontsize=11)
        doc.save(pdf_path)
        doc.close()
        print(f"Created evaluation PDF: {pdf_path}")

    # 2. Save Questions JSON
    questions_path = os.path.join(DATASET_DIR, "eval_questions.json")
    with open(questions_path, "w", encoding="utf-8") as f:
        json.dump(QUESTIONS, f, indent=2)
    print(f"Created evaluation questions: {questions_path} ({len(QUESTIONS)} questions)")


if __name__ == "__main__":
    build_evaluation_dataset()
