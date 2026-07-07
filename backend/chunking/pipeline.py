

from pathlib import Path
from typing import List

from heading_detector import (
    HeadingDetector,
    extract_document_title
)
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()

from semantic_chunker import SemanticChunker

from context_generator import (
    ContextGenerator,
    generate_document_summary
)

from metadata_builder import (
    MetadataBuilder
)

from langchain_ollama import ChatOllama


# Pipeline

class ContextualGraphRAGPipeline:

    def __init__(self, llm, chunk_size=200, overlap=64):
        self.heading_detector = HeadingDetector()
        self.chunker = SemanticChunker(max_chunk_size=chunk_size, overlap=overlap)
        #self.context_generator = ContextGenerator(llm)
        #self.metadata_builder = MetadataBuilder()
        self.llm = llm

    # ------------------------------------------------------

    def process_pdf(self, pdf_path):
        pdf_path = Path(pdf_path)
        print()
        print("=" * 80)
        print("Processing:", pdf_path.name)
        print("=" * 80)
        # ------------------------------------
        # Document Title
        # ------------------------------------
        print()
        print("Extracting title...")
        title = extract_document_title(str(pdf_path))
        print(title)

        # ------------------------------------
        # Heading Detection
        # ------------------------------------
        print()
        print("Detecting headings...")
        headings = self.heading_detector.detect(str(pdf_path))
        print(f"{len(headings)} headings detected")

        # ------------------------------------
        # Semantic Chunking
        # ------------------------------------

        print()
        print("Chunking document...")
        chunks = self.chunker.chunk_document(str(pdf_path), headings, title)
        print(f"{len(chunks)} chunks generated")


    # ------------------------------------------------------

    def process_folder(self, folder):
        folder = Path(folder)
        pdfs = list(folder.glob("*.pdf"))
        all_documents = []
        for pdf in pdfs:
            docs = self.process_pdf(pdf)
            all_documents.extend(docs)
        return all_documents


# ===========================================================
# Utility
# ===========================================================

def pretty_print(document):

    print()

    print("=" * 80)

    print("Chunk ID")

    print(document["id"])

    print()

    print("Metadata")

    print(document["metadata"])

    print()

    print("Context")

    print(document["context"])

    print()

    print("Embedding Text")

    print(document["embedding_text"][:1000])

    print()

    print("=" * 80)


# ===========================================================
# Main
# ===========================================================

if __name__ == "__main__":

    llm = ChatOllama(model="qwen3:14b", temperature=0)

    pipeline = ContextualGraphRAGPipeline(

        llm,

        chunk_size=200,

        overlap=75

    )

    documents = pipeline.process_pdf("TDBalancedGrowthFund-I23062026.pdf")
    print()
    print("=" * 80)
    print(f"Total Chunks : {len(documents)}")
    print("=" * 80)
    pretty_print(documents[0])

