from rag.hybrid_retriver import hybrid_retrieve
from rag.reranker import rerank_documents
from rag.generator import generate_reponse
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query:str
    source:str

@app.post("/chat")
def chat(req:ChatRequest):
    print("Request received:", req.query)
    query = req.query
    source = req.source

    retrieved_docs = hybrid_retrieve(
        query,
        source
    )

    reranked, top_score = rerank_documents(
        query,
        retrieved_docs
    )

    if top_score < 0:

        print("General LLM Mode")

        answer = generate_reponse(
        query
    )

    else:

        print("RAG Mode")

        answer = generate_reponse(
            query,
            reranked
        )

    return {"response": answer}
