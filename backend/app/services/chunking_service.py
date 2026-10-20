"""
Page-aware chunking service.
Splits extracted document text into paragraph- and sentence-aware overlapping chunks.
Tracks accurate page attribution (start_page, end_page, page_number) so citations
never point to pages lacking source text.
"""
import re
from typing import List, Dict, Any, Union
from app.config import settings
from app.services.pdf_service import PageExtractionResult


def split_into_sentences(text: str) -> List[str]:
    """Lightweight sentence splitter that respects punctuation boundaries."""
    # Split on sentence terminals followed by whitespace, keeping delimiters attached
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def chunk_pages(
    pages: List[Union[Dict[str, Any], PageExtractionResult]],
    document_id: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Dict[str, Any]]:
    """
    Chunks extracted pages while preserving page attribution.
    Units: Characters (CHUNK_SIZE=800, CHUNK_OVERLAP=150) for compatibility.
    
    Returns: List of dicts with:
      - chunk_id: str (e.g. 'chunk_0001')
      - document_id: str
      - page_number: int (start_page, for frontend compatibility)
      - start_page: int
      - end_page: int
      - text: str
    """
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP

    chunks: List[Dict[str, Any]] = []
    chunk_counter = 0

    for p in pages:
        if isinstance(p, PageExtractionResult):
            page_num = p.page_number
            raw_text = p.text
        else:
            page_num = p.get("page_number", 1)
            raw_text = p.get("text", "")

        if not raw_text or not raw_text.strip():
            # Skip empty or failed pages
            continue

        text = raw_text.strip()

        # Split into paragraphs by double newlines or single newlines
        paragraphs = [para.strip() for para in text.split("\n\n") if para.strip()]
        if not paragraphs:
            paragraphs = [text]

        buffer = ""
        for para in paragraphs:
            if len(buffer) + len(para) + 1 <= size:
                buffer = f"{buffer} {para}".strip() if buffer else para
            else:
                if buffer:
                    chunk_counter += 1
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_counter:04d}",
                        "document_id": document_id,
                        "page_number": page_num,
                        "start_page": page_num,
                        "end_page": page_num,
                        "text": buffer.strip(),
                    })
                    # Overlap with tail of previous buffer
                    overlap_text = buffer[-overlap:] if len(buffer) > overlap else buffer
                    buffer = f"{overlap_text} {para}".strip()
                    # If even after overlap + para it exceeds size, flush it
                    if len(buffer) > size:
                        # Split paragraph into sentences
                        sentences = split_into_sentences(para)
                        sub_buffer = overlap_text
                        for sent in sentences:
                            if len(sub_buffer) + len(sent) + 1 <= size:
                                sub_buffer = f"{sub_buffer} {sent}".strip() if sub_buffer else sent
                            else:
                                if sub_buffer:
                                    chunk_counter += 1
                                    chunks.append({
                                        "chunk_id": f"chunk_{chunk_counter:04d}",
                                        "document_id": document_id,
                                        "page_number": page_num,
                                        "start_page": page_num,
                                        "end_page": page_num,
                                        "text": sub_buffer.strip(),
                                    })
                                    sub_overlap = sub_buffer[-overlap:] if len(sub_buffer) > overlap else sub_buffer
                                    sub_buffer = f"{sub_overlap} {sent}".strip()
                                else:
                                    # Single sentence longer than chunk_size: hard split
                                    for i in range(0, len(sent), size - overlap):
                                        slice_text = sent[i:i + size]
                                        if slice_text.strip():
                                            chunk_counter += 1
                                            chunks.append({
                                                "chunk_id": f"chunk_{chunk_counter:04d}",
                                                "document_id": document_id,
                                                "page_number": page_num,
                                                "start_page": page_num,
                                                "end_page": page_num,
                                                "text": slice_text.strip(),
                                            })
                                    sub_buffer = ""
                        buffer = sub_buffer
                else:
                    # Paragraph alone is larger than chunk_size
                    sentences = split_into_sentences(para)
                    sub_buffer = ""
                    for sent in sentences:
                        if len(sub_buffer) + len(sent) + 1 <= size:
                            sub_buffer = f"{sub_buffer} {sent}".strip() if sub_buffer else sent
                        else:
                            if sub_buffer:
                                chunk_counter += 1
                                chunks.append({
                                    "chunk_id": f"chunk_{chunk_counter:04d}",
                                    "document_id": document_id,
                                    "page_number": page_num,
                                    "start_page": page_num,
                                    "end_page": page_num,
                                    "text": sub_buffer.strip(),
                                })
                                sub_overlap = sub_buffer[-overlap:] if len(sub_buffer) > overlap else sub_buffer
                                sub_buffer = f"{sub_overlap} {sent}".strip()
                            else:
                                for i in range(0, len(sent), size - overlap):
                                    slice_text = sent[i:i + size]
                                    if slice_text.strip():
                                        chunk_counter += 1
                                        chunks.append({
                                            "chunk_id": f"chunk_{chunk_counter:04d}",
                                            "document_id": document_id,
                                            "page_number": page_num,
                                            "start_page": page_num,
                                            "end_page": page_num,
                                            "text": slice_text.strip(),
                                        })
                                sub_buffer = ""
                    buffer = sub_buffer

        if buffer.strip():
            chunk_counter += 1
            chunks.append({
                "chunk_id": f"chunk_{chunk_counter:04d}",
                "document_id": document_id,
                "page_number": page_num,
                "start_page": page_num,
                "end_page": page_num,
                "text": buffer.strip(),
            })

    return chunks
