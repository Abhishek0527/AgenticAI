import chromadb
import uuid


def _sanitize_metadata_value(value):
    if isinstance(value, (str, int, float, bool)):
        return value

    if value is None:
        return ""

    return str(value)


def _sanitize_metadata(metadata: dict) -> dict:
    sanitized = {}

    for key, value in metadata.items():
        sanitized[key] = _sanitize_metadata_value(value)

    return sanitized


def store_embeddings(
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict]
):
    client = chromadb.PersistentClient(
        path="./chroma_db"
    )

    collection = client.get_or_create_collection(
        name="knowledge_fabric"
    )

    ids = [
        str(uuid.uuid4())
        for _ in chunks
    ]

    sanitized_metadatas = [
        _sanitize_metadata(metadata)
        for metadata in metadatas
    ]

    collection.add(
        embeddings=embeddings,
        documents=chunks,
        ids=ids,
        metadatas=sanitized_metadatas
    )

    print(
        f"Stored {collection.count()} records"
    )
