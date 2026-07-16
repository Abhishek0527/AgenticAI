from rag.embedding import embed_query
from rag.metadata_filters import build_metadata_where
import chromadb


def retrieve_document(
    query: str,
    source: str | None = None,
    metadata_filters: dict | None = None,
    top_k: int = 3
):
    client = chromadb.PersistentClient(path="./chroma_db")

    collection = client.get_or_create_collection(name="knowledge_fabric")

    query_embedding = embed_query(query)
    where = build_metadata_where(
        source,
        metadata_filters
    )

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas"]
    }

    if where:
        query_kwargs["where"] = where

    retrieved = collection.query(**query_kwargs)

    if retrieved["metadatas"][0]:
        print(
            retrieved["metadatas"][0][0]
        )

    print("Vector Source:", source)
    print("Vector Filters:", where)
    print("Retrieved Chunks:", len(retrieved["documents"][0]))

    return {
        "documents": retrieved["documents"][0],
        "metadatas": retrieved["metadatas"][0]
    }

    # print(retrieved["metadatas"])

    # print("Query:", query)
    # # print("Distance:", retrieved["distances"][0][0])

    # best_decison = retrieved["distances"][0][0]

    # Threeshold = 1.5

    # if best_decison > Threeshold:
    #     return None
    # else:
    #     return retrieved["documents"][0]

    # return retrieved['distances']
    # return retrieved["documents"][0]

# Testing retrieve_document
# retrieved_documents = retrieve_document("What is React?")
# print(retrieved_documents)

if __name__ == "__main__":

    retrieve_document(
        "How does password reset work?",
        "jira"
    )
