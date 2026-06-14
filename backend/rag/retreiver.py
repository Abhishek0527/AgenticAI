from rag.embedding import embed_query
import chromadb

def  retrieve_document(query:str, source:str):
    client = chromadb.PersistentClient(path="./chroma_db")

    collection = client.get_or_create_collection(name="knowledge_fabric")

    query_embedding = embed_query(query)


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

    retrieved = collection.query(
        query_embeddings=[query_embedding],
        n_results=10,
        where=where
    )

    print("Vector Source:", source)
    print("Retrieved Chunks:", len(retrieved["documents"][0]))

    return retrieved["documents"][0]

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