from rag.hybrid_retriver import hybrid_retrieve
from rag.reranker import rerank_documents
from rag.generator import generate_reponse
from rag.query_parser import parse_query_metadata

from graph_retrieval import build_graph_context
from rag.context_builder import build_context

from fastapi import FastAPI
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from typing import Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    source: str | None = None
    metadata_filters: dict[str, Any] = Field(
        default_factory=dict
    )


@app.post("/chat")
def chat(req: ChatRequest):

    print("Request received:", req.query)

    parse_result = (
        parse_query_metadata(req.query)
    )

    metadata_filters = dict(
        parse_result.hard_filters
    )
    metadata_filters.update(req.metadata_filters)

    query = parse_result.cleaned_query
    source = req.source

    # Let inferred source_type fully drive retrieval when possible.
    if metadata_filters.get("source"):
        source = metadata_filters["source"]
    elif metadata_filters.get("source_type") in {
        "jira",
        "confluence"
    }:
        source = metadata_filters["source_type"]

    retrieved = hybrid_retrieve(
        query,
        source,
        metadata_filters=metadata_filters,
        soft_filters=parse_result.soft_filters
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

        return {
            "response": answer,
            "citations": {
                "primary": [],
                "parents": [],
                "children": []
            }
        }

    # =====================================
    # ONLY BEST RESULT
    # =====================================

    result = reranked[0]

    document = result["document"]

    metadata = result["metadata"]

    source_id = metadata.get(
        "source"
    )

    source_type = metadata.get(
        "source_type"
    )

    print("\nMetadata:", metadata)
    print("Source ID:", source_id)
    print("Source Type:", source_type)

    graph_result = build_graph_context(
        source_id,
        source_type
    )

    print(
        "\nGraph Result:",
        graph_result
    )

    primary_chunks = [
        document
    ]

    parent_chunks = graph_result[
        "parent_chunks"
    ]

    child_chunks = graph_result[
        "child_chunks"
    ]

    linked_chunks = graph_result[
        "linked_chunks"
    ]

    final_context = build_context(
        primary_chunks,
        parent_chunks,
        child_chunks,
        linked_chunks
    )

    print("\n===== FINAL CONTEXT =====")
    print(final_context)
    print("=========================\n")

    answer = generate_reponse(
        query,
        [final_context]
    )

    return {

        "response": answer,

        "citations": {

            "primary": [
                metadata
            ],

            "parents": graph_result[
                "parent_citations"
            ],

            "children": graph_result[
                "child_citations"
            ],
            "linked": graph_result[
                "linked_citations"
            ]
        }
    }
