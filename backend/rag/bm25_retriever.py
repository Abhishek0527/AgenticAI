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

    results = collection.get(
        where=where,
        include=["metadatas"]
    )

    filtered_docs = results["documents"]
    filtered_metadata = results["metadatas"]

    if not filtered_docs:

        return {
            "documents": [],
            "metadatas": []
        }

    tokenized_docs = [
        doc.lower().split()
        for doc in filtered_docs
    ]

    bm25 = BM25Okapi(tokenized_docs)

    scores = bm25.get_scores(
        query.lower().split()
    )

    ranked = sorted(
        zip(
            filtered_docs,
            filtered_metadata,
            scores
        ),
        key=lambda x: x[2],
        reverse=True
    )

    top_docs = []
    top_metadata = []

    for doc, metadata, score in ranked[:top_k]:

        top_docs.append(doc)
        top_metadata.append(metadata)

    return {
        "documents": top_docs,
        "metadatas": top_metadata
    }