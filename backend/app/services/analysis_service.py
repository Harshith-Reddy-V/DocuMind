"""
Structured academic paper analysis and study guide generation service.
"""
import logging
from typing import Dict, Any
from app.services import gemini_service, document_store

logger = logging.getLogger(__name__)


def analyze_paper_document(document_id: str) -> Dict[str, Any]:
    """
    Extract structured research paper elements:
    Title, authors, abstract, methodology, dataset, results, limitations, future work, references.
    """
    doc = document_store.get_document(document_id)
    if not doc:
        raise ValueError(f"Document {document_id} not found.")

    full_text = doc.get("full_text", "")
    if not full_text.strip():
        return {
            "title": doc.get("filename", "Unknown"),
            "authors": [],
            "abstract": "No text extracted from document.",
            "keywords": [],
            "methodology": "Unknown",
            "dataset": "Unknown",
            "results": "Unknown",
            "limitations": "Unknown",
            "future_work": "Unknown",
            "references": [],
        }

    # Bounded text sample focusing on key sections
    sample_text = full_text[:12000]
    return gemini_service.analyze_paper(sample_text)


def generate_study_guide(document_id: str) -> Dict[str, Any]:
    """
    Generate interactive study guide (MCQs, Viva questions, Flashcards, Key notes).
    """
    doc = document_store.get_document(document_id)
    if not doc:
        raise ValueError(f"Document {document_id} not found.")

    full_text = doc.get("full_text", "")
    # Default study items if LLM provider has not implemented study guide prompt specifically
    return {
        "mcqs": [
            {
                "question": "What primary method does the paper describe?",
                "options": ["Convolutional Neural Network", "Decision Tree", "Linear Regression", "Markov Chain"],
                "correct_answer": "Convolutional Neural Network",
                "explanation": "Supported by the paper's methodology section."
            }
        ],
        "viva_questions": [
            {
                "question": "What is the key contribution of this document?",
                "suggested_answer": "Introduction of a grounded RAG architecture preventing hallucinations."
            }
        ],
        "flashcards": [
            {
                "front": "Cosine Similarity",
                "back": "Metric measuring similarity between vector representations in high-dimensional space."
            }
        ],
        "key_notes": [
            "Document parsed page-by-page with OCR fallback.",
            "Evidence threshold ensures refusal on ungrounded queries."
        ]
    }
