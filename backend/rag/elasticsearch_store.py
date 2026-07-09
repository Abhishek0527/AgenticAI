from __future__ import annotations

import os
from typing import Any

from elasticsearch import Elasticsearch


DEFAULT_INDEX_NAME = "knowledge_fabric"
DEFAULT_VECTOR_DIMS = 384


def get_index_name() -> str:
    return os.getenv(
        "ELASTICSEARCH_INDEX",
        DEFAULT_INDEX_NAME
    )


def get_es_client() -> Elasticsearch:
    hosts = os.getenv(
        "ELASTICSEARCH_URL",
        "http://localhost:9200"
    )
    api_key = os.getenv("ELASTICSEARCH_API_KEY")
    username = os.getenv("ELASTICSEARCH_USERNAME")
    password = os.getenv("ELASTICSEARCH_PASSWORD")

    kwargs: dict[str, Any] = {
        "hosts": [hosts]
    }

    if api_key:
        kwargs["api_key"] = api_key
    elif username and password:
        kwargs["basic_auth"] = (
            username,
            password
        )

    return Elasticsearch(**kwargs)


def ensure_index(
    client: Elasticsearch,
    index_name: str | None = None,
    vector_dims: int = DEFAULT_VECTOR_DIMS
) -> str:
    resolved_index = index_name or get_index_name()

    if client.indices.exists(index=resolved_index):
        return resolved_index

    client.indices.create(
        index=resolved_index,
        mappings={
            "properties": {
                "chunk_text": {
                    "type": "text"
                },
                "embedding": {
                    "type": "dense_vector",
                    "dims": vector_dims,
                    "index": False
                },
                "metadata": {
                    "type": "flattened"
                },
                "source": {
                    "type": "keyword"
                },
                "source_type": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "document": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                }
            }
        }
    )

    return resolved_index


def build_filter_clauses(
    source: str | None = None,
    metadata_filters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    clauses: list[dict[str, Any]] = []

    if source:
        clauses.append(
            {
                "term": {
                    "source": source
                }
            }
        )

    if not metadata_filters:
        return clauses

    for key, value in metadata_filters.items():
        if value is None:
            continue

        field_name = (
            key
            if key in {"source", "source_type"}
            else f"metadata.{key}"
        )

        if isinstance(value, list):
            clauses.append(
                {
                    "terms": {
                        field_name: value
                    }
                }
            )
        else:
            clauses.append(
                {
                    "term": {
                        field_name: value
                    }
                }
            )

    return clauses


def normalize_hit(hit: dict[str, Any]) -> dict[str, Any]:
    source = hit.get("_source", {})
    metadata = dict(source.get("metadata", {}))

    metadata.setdefault(
        "source",
        source.get("source")
    )
    metadata.setdefault(
        "source_type",
        source.get("source_type")
    )
    metadata.setdefault(
        "title",
        source.get("title")
    )
    metadata.setdefault(
        "document",
        source.get("document")
    )

    return {
        "document": source.get("chunk_text", ""),
        "metadata": metadata,
        "score": hit.get("_score", 0.0)
    }
