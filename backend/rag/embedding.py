import os
from sentence_transformers import SentenceTransformer

# Load model from local directory (no HF Hub download needed)
model_dir = os.path.join(os.path.dirname(__file__), "..", "models", "all-MiniLM-L6-v2")
model = SentenceTransformer(model_dir)

def embed_chunks(chunks:list[str]) -> list[list[float]]:

    embeddings = model.encode(chunks)

    return embeddings

def embed_query(query:str):

    embed_query = model.encode(query)
    return embed_query

# Testing embed_query
# query = "What is React?"
# query_embedding = embed_query(query)
# print(query_embedding)