import chromadb
import uuid


def store_embeddings(
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    ids: list[str] = None
):

    client = chromadb.PersistentClient(
        path="./chroma_db"
    )

    collection = client.get_or_create_collection(
        name="knowledge_fabric"
    )

    if ids is None:
        ids = [
            str(uuid.uuid4())
            for _ in chunks
        ]

    collection.add(
        embeddings=embeddings,
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )

    print(
        f"Stored {collection.count()} records"
    )
    return ids