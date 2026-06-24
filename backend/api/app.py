from rag.hybrid_retriver import hybrid_retrieve
from rag.reranker import rerank_documents
from rag.generator import generate_reponse
from graph_context import get_graph_context
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

    retrieved = hybrid_retrieve(
        query,
        source
    )

    reranked, top_score = rerank_documents(
        query,
        retrieved["documents"],
        retrieved["metadatas"]
    )



    if top_score < 0:

         answer = generate_reponse(
            query
        )

    else:

        enriched_context = []

        for result in reranked:

            enriched_context.append(
                result["document"]
            )

            metadata = result.get(
                "metadata",
                {}
            )
            if not metadata:
                continue

            source_id = metadata.get(
                "source"
            )

            source_type = metadata.get(
                "source_type"
            )

            if not source_id or not source_type:
                continue

            print("\nMetadata:", metadata)
            print("Source:", source_id)
            print("Source Type:", source_type)

            graph_context = get_graph_context(
                source_id,
                source_type
            )

            print("\nGraph Context:", graph_context)

            parents = graph_context.get(
                "parents",
                []
            )

            children = graph_context.get(
                "children",
                []
            )

            if parents:

                enriched_context.append(
                    "Parent Context: "
                    + ", ".join(parents)
                )

            if children:

                enriched_context.append(
                    "Child Context: "
                    + ", ".join(children)
                )

        print("\n===== ENRICHED CONTEXT =====")

        for item in enriched_context:
            print(item)
            print("-" * 50)

        print("============================\n")

        answer = generate_reponse(
            query,
            enriched_context
        )

    return {
        "response": answer
    }
