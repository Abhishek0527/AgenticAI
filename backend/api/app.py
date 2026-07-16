from rag.hybrid_retriver import hybrid_retrieve
from rag.reranker import rerank_documents
from rag.generator import generate_reponse
from rag.query_parser import parse_query_metadata

from graph_retrieval import build_graph_context
from rag.context_builder import build_context
from source_retriever import retrieve_by_source

from fastapi import FastAPI
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
import re

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

    retrieval_query = parse_result.cleaned_query
    answer_query = req.query
    source = req.source

    retrieved = hybrid_retrieve(
        retrieval_query,
        source,
        metadata_filters=metadata_filters,
        soft_filters=parse_result.soft_filters
    )

    reranked, top_score = rerank_documents(
        answer_query,
        retrieved["documents"],
        retrieved["metadatas"]
    )

    if top_score < 0 and not retrieved["documents"]:

        answer = generate_reponse(
            answer_query
        )

        return {
            "response": answer,
            "citations": {
                "primary": [],
                "parents": [],
                "children": []
            }
        }

    list_intent = _is_list_intent(
        answer_query
    )

    if list_intent:
        primary_chunks = []
        parent_chunks = []
        child_chunks = []
        linked_chunks = []
        primary_citations = []
        parent_citations = []
        child_citations = []
        linked_citations = []
        seen_sources = set()

        for result in reranked[:5]:
            metadata = result["metadata"]
            source_id = metadata.get("source")
            source_type = metadata.get(
                "source_type"
            )

            if not source_id or source_id in seen_sources:
                continue

            seen_sources.add(source_id)
            primary_citations.append(metadata)

            primary_result = retrieve_by_source(
                source_id
            )
            primary_chunks.extend(
                primary_result["documents"] or [
                    result["document"]
                ]
            )

            graph_result = build_graph_context(
                source_id,
                source_type
            )

            parent_chunks.extend(
                graph_result["parent_chunks"]
            )
            child_chunks.extend(
                graph_result["child_chunks"]
            )
            linked_chunks.extend(
                graph_result["linked_chunks"]
            )
            parent_citations.extend(
                graph_result["parent_citations"]
            )
            child_citations.extend(
                graph_result["child_citations"]
            )
            linked_citations.extend(
                graph_result["linked_citations"]
            )

        metadata = primary_citations[0]
    else:
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

        primary_result = retrieve_by_source(
            source_id
        ) if source_id else {
            "documents": [document]
        }

        primary_chunks = primary_result[
            "documents"
        ] or [document]

        parent_chunks = graph_result[
            "parent_chunks"
        ]

        child_chunks = graph_result[
            "child_chunks"
        ]

        linked_chunks = graph_result[
            "linked_chunks"
        ]
        primary_citations = [metadata]
        parent_citations = graph_result[
            "parent_citations"
        ]
        child_citations = graph_result[
            "child_citations"
        ]
        linked_citations = graph_result[
            "linked_citations"
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
        answer_query,
        [final_context]
    )

    return {

        "response": answer,

        "citations": {

            "primary": primary_citations,
            "parents": _dedupe_list(
                parent_citations
            ),
            "children": _dedupe_list(
                child_citations
            ),
            "linked": _dedupe_list(
                linked_citations
            )
        }
    }


def _is_list_intent(query: str) -> bool:
    lowered = query.lower()
    return bool(
        re.search(
            r"\b(which|list|show all|all|what are)\b",
            lowered
        )
    )


def _dedupe_list(values: list[Any]) -> list[Any]:
    deduped = []
    for value in values:
        if value in deduped:
            continue
        deduped.append(value)
    return deduped
