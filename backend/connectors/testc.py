import chromadb

client = chromadb.PersistentClient(path="../chroma_db")

collection = client.get_collection("knowledge_fabric")

results = collection.get(
    where={
        "source_type": "confluence"
    }
)

print(results["documents"])