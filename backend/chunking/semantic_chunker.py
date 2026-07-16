
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import fitz
import nltk
from nltk.tokenize import sent_tokenize
import re
from .tokenizer import BPETokenizer


# ============================================================
# Models
# ============================================================

@dataclass
class Chunk:

    document_title: str

    h1: Optional[str]

    h2: Optional[str]

    h3: Optional[str]

    page_start: int

    page_end: int

    text: str

    metadata: dict


# ============================================================
# Semantic Chunker
# ============================================================

class SemanticChunker:

    def __init__(

            self,

            max_chunk_size: int = 200,

            overlap: int = 100

    ):
        print("Inside SemanticChunker")
        self.tokenizer = BPETokenizer()
        self.max_chunk_tokens = max_chunk_size
        self.overlap_tokens = overlap

    # --------------------------------------------------------

    def chunk_document(

            self,

            pdf_path,

            headings,

            document_title

    ) -> List[Chunk]:
        print("Inside Chunk Document")

        pages = self._extract_pages(pdf_path)

        sections = self._split_into_sections(

            pages,

            headings

        )

        chunks = []

        current_h1 = None
        current_h2 = None
        current_h3 = None

        for section in sections:

            heading = section["heading"]

            if heading:

                if heading.level == 1:

                    current_h1 = heading.text

                    current_h2 = None

                    current_h3 = None

                elif heading.level == 2:

                    current_h2 = heading.text

                    current_h3 = None

                elif heading.level == 3:

                    current_h3 = heading.text

            semantic_chunks = self._semantic_split(

                section["text"]

            )

            for chunk in semantic_chunks:

                chunks.append(

                    Chunk(

                        document_title=document_title,

                        h1=current_h1,

                        h2=current_h2,

                        h3=current_h3,

                        page_start=section["page"],

                        page_end=section["page"],

                        text=chunk,

                        metadata={

                            "document": document_title,

                            "h1": current_h1,

                            "h2": current_h2,

                            "h3": current_h3,

                            "page": section["page"]

                        }

                    )

                )
        for chunk in chunks:
            print("Chunks - ", chunk)
        return chunks

    # --------------------------------------------------------

    def _extract_pages(self, pdf_path):

        doc = fitz.open(pdf_path)

        pages = []

        for page_number, page in enumerate(doc):

            text = page.get_text()

            pages.append(

                {

                    "page": page_number + 1,

                    "text": text

                }

            )

        return pages

    # --------------------------------------------------------

    def _split_into_sections(

            self,

            pages,

            headings

    ):

        sections = []

        heading_lookup = {

            (h.page, h.text): h

            for h in headings

        }

        current_heading = None

        current_text = ""

        current_page = 1

        heading_texts = {

            h.text

            for h in headings

        }

        for page in pages:

            lines = page["text"].split("\n")

            for line in lines:

                line = line.strip()

                if line in heading_texts:

                    if current_text:

                        sections.append(

                            {

                                "heading": current_heading,

                                "text": current_text,

                                "page": current_page

                            }

                        )

                        current_text = ""

                    current_heading = heading_lookup.get(

                        (page["page"], line)

                    )

                    current_page = page["page"]

                else:

                    current_text += line + "\n"

        if current_text:

            sections.append(

                {

                    "heading": current_heading,

                    "text": current_text,

                    "page": current_page

                }

            )

        return sections

    # --------------------------------------------------------

    def _semantic_split(self, text):
        """
        Split text into semantic chunks using BPE token count
        instead of character count.
        """

        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt")

        try:
            nltk.data.find("tokenizers/punkt_tab/english")
        except LookupError:
            nltk.download("punkt_tab")

        try:
            sentences = sent_tokenize(text)
        except LookupError:
            # Fallback for environments where punkt assets are still incomplete.
            sentences = [
                sentence.strip()
                for sentence in re.split(
                    r"(?<=[.!?])\s+",
                    text
                )
                if sentence.strip()
            ]

        chunks = []

        current_sentences = []

        for sentence in sentences:

            # Candidate chunk after adding this sentence
            candidate = " ".join(current_sentences + [sentence])

            token_count = self.tokenizer.count_tokens(candidate)

            if token_count <= self.max_chunk_tokens:

                current_sentences.append(sentence)

            else:

                if current_sentences:

                    chunk = " ".join(current_sentences)

                    chunks.append(chunk)

                    # Keep token overlap
                    overlap = self.tokenizer.get_overlap_text(
                        chunk,
                        self.overlap_tokens
                    )
                    current_sentences = [overlap, sentence]

                else:
                    # Single sentence is larger than max chunk size
                    chunks.append(sentence)

                    current_sentences = []

        if current_sentences:
            chunks.append(" ".join(current_sentences))

        return chunks


# ============================================================
# Example
# ============================================================

if __name__ == "__main__":

    from heading_detector import (

        HeadingDetector,

        extract_document_title

    )

    pdf = "sample.pdf"

    detector = HeadingDetector()

    headings = detector.detect(pdf)

    title = extract_document_title(pdf)

    chunker = SemanticChunker(

        max_chunk_size=200,

        overlap=64

    )

    chunks = chunker.chunk_document(

        pdf,

        headings,

        title

    )

    print()

    print("=" * 60)

    print("Generated Chunks")

    print("=" * 60)

    print()

    for idx, chunk in enumerate(chunks):

        print(f"Chunk {idx+1}")

        print("-" * 40)

        print("Document :", chunk.document_title)

        print("H1       :", chunk.h1)

        print("H2       :", chunk.h2)

        print("H3       :", chunk.h3)

        print("Page     :", chunk.page_start)

        print()

        print(chunk.text[:500])

        print()

        print("=" * 60)
