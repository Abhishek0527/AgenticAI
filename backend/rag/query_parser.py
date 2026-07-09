from __future__ import annotations

import re
from typing import Any


STATUS_PATTERNS = {
    "done": "Done",
    "closed": "Done",
    "completed": "Done",
    "in progress": "In Progress",
    "open": "Open",
    "todo": "To Do",
    "to do": "To Do",
}

ISSUE_TYPE_PATTERNS = {
    "bug": "Bug",
    "task": "Task",
    "story": "Story",
    "epic": "Epic",
}


def parse_query_metadata(
    query: str
) -> tuple[str, dict[str, Any]]:
    """
    Extract lightweight metadata filters from a natural-language query.
    Returns a cleaned query plus inferred filters.
    """

    original_query = query.strip()
    lowered_query = original_query.lower()
    metadata_filters: dict[str, Any] = {}

    if "jira" in lowered_query:
        metadata_filters["source_type"] = "jira"

    if "confluence" in lowered_query:
        metadata_filters["source_type"] = "confluence"

    if "pdf" in lowered_query or "document" in lowered_query:
        metadata_filters["source_type"] = "pdf"

    for pattern, status in STATUS_PATTERNS.items():
        if pattern in lowered_query:
            metadata_filters["status"] = status
            break

    for pattern, issue_type in ISSUE_TYPE_PATTERNS.items():
        if re.search(rf"\b{re.escape(pattern)}s?\b", lowered_query):
            metadata_filters["issue_type"] = issue_type
            break

    ticket_match = re.search(
        r"\b([A-Z][A-Z0-9]+-\d+)\b",
        original_query
    )
    if ticket_match:
        metadata_filters["source"] = ticket_match.group(1)

    page_match = re.search(
        r"\bpage\s+(\d+)\b",
        lowered_query
    )
    if page_match:
        metadata_filters["page"] = int(
            page_match.group(1)
        )

    cleaned_query = _remove_filter_terms(
        original_query
    )

    return cleaned_query or original_query, metadata_filters


def _remove_filter_terms(query: str) -> str:
    cleaned = query

    removable_patterns = [
        r"\bjira\b",
        r"\bconfluence\b",
        r"\bpdf\b",
        r"\bdocument\b",
        r"\bdone\b",
        r"\bclosed\b",
        r"\bcompleted\b",
        r"\bin progress\b",
        r"\bopen\b",
        r"\btodo\b",
        r"\bto do\b",
        r"\bbugs?\b",
        r"\btasks?\b",
        r"\bstor(?:y|ies)\b",
        r"\bepics?\b",
        r"\bpage\s+\d+\b",
        r"\b[A-Z][A-Z0-9]+-\d+\b",
    ]

    for pattern in removable_patterns:
        cleaned = re.sub(
            pattern,
            " ",
            cleaned,
            flags=re.IGNORECASE
        )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned
    ).strip(" ,.-")

    return cleaned
