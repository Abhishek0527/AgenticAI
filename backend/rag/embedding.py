from sentence_transformers import SentenceTransformer

def embed_chunks(chunks:list[str]) -> list[list[float]]:
    model_name="all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)

    embeddings = model.encode(chunks)

    return embeddings

def embed_query(query:str):
    model_name = "all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)
    embed_query = model.encode(query)
    return embed_query

# Testing embed_query
# query = "What is React?"
# query_embedding = embed_query(query)
# print(query_embedding)