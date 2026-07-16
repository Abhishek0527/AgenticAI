from __future__ import annotations

from typing import Any


def build_metadata_where(
    source: str | None = None,
    metadata_filters: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """
    Build a metadata filter by combining optional source scoping with
    optional user-provided metadata filters.
    """

    clauses: list[dict[str, Any]] = []

    if source == "jira":
        clauses.append({
            "source_type": "jira"
        })
    elif source == "confluence":
        clauses.append({
            "source_type": "confluence"
        })
    elif source:
        clauses.append({
            "source": source
        })

    if metadata_filters:
        for key, value in metadata_filters.items():
            if value is None:
                continue
            if isinstance(value, list):
                clauses.append({
                    key: {
                        "$in": value
                    }
                })
                continue
            clauses.append({
                key: value
            })

    if not clauses:
        return None

    if len(clauses) == 1:
        return clauses[0]

    return {
        "$and": clauses
    }
