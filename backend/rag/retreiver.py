from rag.embedding import embed_query
import chromadb

def  retrieve_document(query:str):
    client = chromadb.Client()

    collection = client.get_or_create_collection(name="pdf_collection")

    query_embedding = embed_query(query)

    retrieved = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    best_decison = retrieved["distances"][0][0]

    Threeshold = 1.2

    if best_decison > Threeshold:
        return None
    else:
        return retrieved["documents"][0]
    
    # return retrieved['distances']
    # return retrieved["documents"][0]

# Testing retrieve_document
# retrieved_documents = retrieve_document("What is React?")
# print(retrieved_documents)