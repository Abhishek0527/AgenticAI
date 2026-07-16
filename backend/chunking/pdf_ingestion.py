from __future__ import annotations

from pathlib import Path

from .heading_detector import HeadingDetector, extract_document_title
from .semantic_chunker import SemanticChunker


def build_pdf_chunks_with_metadata(
    pdf_path: str,
    chunk_size: int = 200,
    overlap: int = 75
) -> tuple[list[str], list[dict]]:
    """
    Convert a PDF into semantic chunks plus metadata using the
    experimental chunking strategy.
    """

    resolved_path = Path(pdf_path)

    title = extract_document_title(str(resolved_path))

    detector = HeadingDetector()
    headings = detector.detect(str(resolved_path))

    chunker = SemanticChunker(
        max_chunk_size=chunk_size,
        overlap=overlap
    )

    chunk_objects = chunker.chunk_document(
        str(resolved_path),
        headings,
        title
    )

    chunks: list[str] = []
    metadatas: list[dict] = []

    for index, chunk in enumerate(chunk_objects):
        chunks.append(chunk.text)
        metadatas.append(
            {
                "source_type": "pdf",
                "source": resolved_path.name,
                "title": chunk.document_title or resolved_path.name,
                "document": chunk.document_title or resolved_path.name,
                "project": "learning",
                "chunk_index": index,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "page": chunk.metadata.get("page"),
                "h1": chunk.h1,
                "h2": chunk.h2,
                "h3": chunk.h3,
            }
        )

    return chunks, metadatas
