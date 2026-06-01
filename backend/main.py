from rag.generator import generate_reponse
from rag.retreiver import retrieve_document
from rag.vectorstore import store_embeddings
from rag.embedding import embed_chunks
from rag.document_loader import load_pdf
from rag.chunker import chunk_text

def main():
    pdf_path = r"C:\Users\Owner\Downloads\reactpdf.pdf"

    text = load_pdf(pdf_path)

    chunks = chunk_text(text)

    # print(f"Total Chunks: {len(chunks)}")

    embeddings = embed_chunks(chunks)

    # print(f"Total Embeddings: {len(embeddings)}")

    store_embeddings(chunks,embeddings)

    query ="What is React?"

    result = retrieve_document(query)

    # print(result)

    answer = generate_reponse(query,result)

    print(answer)

    # print(f"Total Chunks: {len(chunks)}")
    # print(f"Embeddings Shape: {embeddings.shape}")
    # print("\nFirst Chunk:\n")
    # print(chunks[0])


if __name__ == "__main__":
    main()
