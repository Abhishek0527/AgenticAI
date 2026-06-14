import chromadb

client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    "knowledge_fabric"
)

print(collection.count())

results = collection.get(
    where={
        "source_type": "jira"
    }
)

print(len(results["documents"]))