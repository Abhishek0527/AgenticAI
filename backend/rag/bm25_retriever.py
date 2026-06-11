from rank_bm25 import BM25Okapi
import chromadb


client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="pdf_collection"
)


def bm25_retrieve(
    query: str,
    source: str,
    top_k: int = 10
):
   
    if not source.lower().endswith(".pdf"):
        filtered_docs = collection.get(
            where={
                "source_type": source
            }
        )["documents"]
    else:
        filtered_docs = collection.get(
            where={
                "source": source            }
        )["documents"]

    

    tokenized_docs = [
        doc.lower().split()
        for doc in filtered_docs
    ]

    bm25 = BM25Okapi(tokenized_docs)

    tokenized_query = query.lower().split()

    scores = bm25.get_scores(
        tokenized_query
    )

    ranked = sorted(
        zip(filtered_docs, scores),
        key=lambda x: x[1],
        reverse=True
    )

    top_docs = [
        doc
        for doc, score in ranked[:top_k]
    ]

    print("BM25 Source:", source)
    print("BM25 Docs:", len(filtered_docs))

    return top_docs
