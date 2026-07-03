import chromadb


client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="knowledge_fabric"
)


def retrieve_by_source(
    source_id: str
):

    result = collection.get(
        where={
            "source": source_id
        },
        include=[
            "documents",
            "metadatas"
        ]
    )

    return {
        "documents": result["documents"],
        "metadatas": result["metadatas"]
    }


if __name__ == "__main__":

    result = retrieve_by_source(
        "SCRUM-11"
    )

    print(
        f"Chunks: {len(result['documents'])}"
    )

    print()

    for doc in result["documents"]:

        print(doc)
        print("-" * 100)