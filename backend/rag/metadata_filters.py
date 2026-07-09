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

    where: dict[str, Any] = {}

    if source == "jira":
        where["source_type"] = "jira"
    elif source == "confluence":
        where["source_type"] = "confluence"
    elif source:
        where["source"] = source

    if metadata_filters:
        for key, value in metadata_filters.items():
            if value is None:
                continue
            where[key] = value

    return where or None
