import chromadb


def store_embeddings(chunks:list[str],embeddings:list[list[float]]):
    client = chromadb.Client()
    collection = client.get_or_create_collection(name="pdf_collection")

    ids = []

    for i in range(len(chunks)):
        ids.append(str(i))

    collection.add(
        embeddings = embeddings,
        documents=chunks,
        ids = ids
    )

    # return collection
    print(f"Stored {collection.count()} records")