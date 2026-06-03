from rag.vectorstore import store_embeddings
from rag.embedding import embed_chunks
from rag.chunker import chunk_text
from rag.document_loader import load_pdf

def ingest():
    pdf_path = r"C:\Users\Owner\Downloads\reactpdf.pdf"

    text = load_pdf(pdf_path)

    chunks = chunk_text(text)

    # print(f"Total Chunks: {len(chunks)}")

    embeddings = embed_chunks(chunks)

    # print(f"Total Embeddings: {len(embeddings)}")

    store_embeddings(chunks,embeddings)

if __name__ == "__main__":
    ingest()