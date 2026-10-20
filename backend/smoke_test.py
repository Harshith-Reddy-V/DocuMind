"""
Real-Gemini Smoke Test Script.
Tests live Google Gemini API connectivity, embeddings, generation, and multimodal OCR
when valid GEMINI_API_KEY credentials are provided.
"""
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.services.gemini_service import RealGeminiProvider, EXACT_REFUSAL_SENTENCE


def run_smoke_test():
    print("=" * 60)
    print("DocuMind Live Gemini API Smoke Test")
    print("=" * 60)

    api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
    if not api_key:
        print("[SKIPPED] GEMINI_API_KEY is not configured.")
        print("To run live Gemini smoke tests:")
        print("1. Set GEMINI_API_KEY in backend/.env or your environment variables.")
        print("2. Re-run: python smoke_test.py")
        print("=" * 60)
        return

    provider = RealGeminiProvider()
    print(f"Configured Generation Model: {settings.GEMINI_GENERATION_MODEL}")
    print(f"Configured Embedding Model:  {settings.GEMINI_EMBEDDING_MODEL}")
    print("-" * 60)

    # Test 1: Real Embedding
    print("[1/5] Testing real embedding generation...")
    try:
        vec = provider.embed_text("DocuMind academic RAG system", task_type="RETRIEVAL_QUERY")
        print(f"  --> SUCCESS: Received embedding vector of dimension {len(vec)}")
    except Exception as e:
        print(f"  --> FAILED: {e}")

    # Test 2: Real Grounded Generation (Answerable)
    print("[2/5] Testing grounded answer generation (Answer exists)...")
    context = [{
        "chunk_id": "chunk_001",
        "page_number": 1,
        "text": "The proposed system uses a CNN model for document representation."
    }]
    try:
        ans = provider.generate_grounded_answer("What model does the system use?", context)
        print(f"  --> SUCCESS: Answerable={ans.get('answerable')}")
        print(f"      Answer: {ans.get('answer')}")
        print(f"      Citations: {ans.get('cited_chunk_ids')}")
    except Exception as e:
        print(f"  --> FAILED: {e}")

    # Test 3: Real Grounded Generation (Unanswerable Refusal)
    print("[3/5] Testing grounded refusal (Answer absent)...")
    try:
        ref = provider.generate_grounded_answer("Who invented the microscope?", context)
        print(f"  --> SUCCESS: Answerable={ref.get('answerable')}")
        print(f"      Answer: {ref.get('answer')}")
        assert ref.get("answer") == EXACT_REFUSAL_SENTENCE
    except Exception as e:
        print(f"  --> FAILED / ASSERTION ERROR: {e}")

    # Test 4: Real Summarization
    print("[4/5] Testing live summarization...")
    try:
        summary = provider.generate_summary("DocuMind is an academic assistant that prevents hallucinations using RAG.")
        print(f"  --> SUCCESS: Short summary: {summary.get('short_summary')[:100]}...")
    except Exception as e:
        print(f"  --> FAILED: {e}")

    # Test 5: Multimodal OCR
    print("[5/5] Testing multimodal vision / OCR...")
    try:
        import pymupdf
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((50, 72), "DocuMind OCR Test", fontsize=14)
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        doc.close()

        ocr_text = provider.extract_text_from_image(img_bytes)
        print(f"  --> SUCCESS: OCR transcribed: '{ocr_text.strip()}'")
    except Exception as e:
        print(f"  --> FAILED: {e}")

    print("=" * 60)
    print("Smoke test run completed.")
    print("=" * 60)


if __name__ == "__main__":
    run_smoke_test()
