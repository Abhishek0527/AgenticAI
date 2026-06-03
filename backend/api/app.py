from rag.generator import generate_reponse
from rag.retreiver import retrieve_document
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

@app.post("/chat")
def chat(req:ChatRequest):
    print("Request received:", req.query)
    query = req.query
    result = retrieve_document(query)
    answer = generate_reponse(query,result)
    return {"response":answer}

