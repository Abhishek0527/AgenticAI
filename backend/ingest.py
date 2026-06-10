import os

from rag.chunker import chunk_text
from rag.document_loader import load_confluence_pages, load_pdf
from rag.embedding import embed_chunks
from rag.vectorstore import store_embeddings

from dotenv import load_dotenv
load_dotenv()

PDF_FOLDER = "./pdf_documents"
USE_CONFLUENCE = os.getenv("ENABLE_CONFLUENCE_INGEST", "true").lower() in {"1", "true", "yes"}


def _store_text(source_name, text):
    chunks = chunk_text(text)

    if not chunks:
        print(f"Skipped: {source_name} (no text extracted)")
        return

    metadatas = [
        {
            "source": source_name,
            "chunk_index": index,
        }
        for index, _ in enumerate(chunks)
    ]

    embeddings = embed_chunks(chunks)
    store_embeddings(chunks, embeddings, metadatas)

    print(f"Finished: {source_name}")
    print(f"Chunks Stored: {len(chunks)}")


def ingest():
    pdf_files = [
        file
        for file in os.listdir(PDF_FOLDER)
        if file.endswith(".pdf")
    ]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_FOLDER, pdf_file)
        print(f"\nProcessing PDF: {pdf_file}")
        text = load_pdf(pdf_path)
        _store_text(pdf_file, text)

    if USE_CONFLUENCE:
        print("\nChecking Confluence pages...")

        try:
            confluence_pages = load_confluence_pages()
        except Exception as exc:
            print(f"Confluence ingestion skipped: {exc}")
            return

        for source_name, text in confluence_pages:
            print(f"\nProcessing Confluence page: {source_name}")
            _store_text(source_name, text)


if __name__ == "__main__":
    ingest()

# def ingest():
#     pdf_path = r"C:\Users\Owner\Downloads\reactpdf.pdf"

#     source = os.path.basename(pdf_path)

#     metadatas = []



#     text = load_pdf(pdf_path)

#     chunks = chunk_text(text)

#     for _ in chunks:
#         metadatas.append(
#             {
#                 "source": source
#             }
#     )

#     # print(f"Total Chunks: {len(chunks)}")

#     embeddings = embed_chunks(chunks)

#     # print(f"Total Embeddings: {len(embeddings)}")

#     store_embeddings(chunks,embeddings,metadatas)
#  ---------------this is used for single source of pdf-----------