from rag.embedding import embed_query
import chromadb

def  retrieve_document(query:str):
    client = chromadb.PersistentClient(path="./chroma_db")

    collection = client.get_or_create_collection(name="pdf_collection")

    query_embedding = embed_query(query)

    retrieved = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    print("Query:", query)
    print("Distance:", retrieved["distances"][0][0])

    best_decison = retrieved["distances"][0][0]

    Threeshold = 1.5

    if best_decison > Threeshold:
        return None
    else:
        return retrieved["documents"][0]
    
    # return retrieved['distances']
    # return retrieved["documents"][0]

# Testing retrieve_document
# retrieved_documents = retrieve_document("What is React?")
# print(retrieved_documents)