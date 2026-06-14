from rank_bm25 import BM25Okapi
import chromadb


client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="knowledge_fabric"
)


def bm25_retrieve(
    query: str,
    source: str,
    top_k: int = 10
):

    if source == "jira":

        where = {
        "source_type": "jira"
    }

    elif source == "confluence":

        where = {
            "source_type": "confluence"
        }

    else:

        where = {
            "source": source
        }

    filtered_docs = collection.get(
        where=where
    )["documents"]

    if not filtered_docs:

        print("No BM25 docs found")

        return []

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
