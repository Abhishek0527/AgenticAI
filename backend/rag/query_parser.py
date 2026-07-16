from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

import anthropic
from dotenv import load_dotenv
from rag.entity_resolver import resolve_query_entity

load_dotenv()


STATUS_PATTERNS = {
    "done": "Done",
    "closed": "Done",
    "resolved": "Done",
    "completed": "Done",
    "in progress": "In Progress",
    "open": [
        "Open",
        "To Do",
        "In Progress",
    ],
    "todo": "To Do",
    "to do": "To Do",
}

ISSUE_TYPE_PATTERNS = {
    "bug": "Bug",
    "task": "Task",
    "story": "Story",
    "epic": "Epic",
}

ALLOWED_FILTER_KEYS = {
    "source_type",
    "source",
    "status",
    "issue_type",
    "page",
    "project",
    "parent_key",
    "parent_title",
    "section_type",
    "title",
    "document",
    "h1",
    "h2",
    "h3",
}

SOURCE_TYPE_VALUES = {
    "jira",
    "confluence",
    "pdf",
}

LLM_MODEL = "claude-haiku-4-5"

_anthropic_client = None


@dataclass
class QueryParseResult:
    cleaned_query: str
    hard_filters: dict[str, Any] = field(
        default_factory=dict
    )
    soft_filters: dict[str, Any] = field(
        default_factory=dict
    )


def _get_anthropic_client():
    global _anthropic_client

    if _anthropic_client is not None:
        return _anthropic_client

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    _anthropic_client = anthropic.Anthropic(
        api_key=api_key
    )
    return _anthropic_client


def parse_query_metadata(
    query: str
) -> QueryParseResult:
    """
    Hybrid parser:
    1. Apply deterministic rule extraction.
    2. Ask an LLM for richer natural-language understanding.
    3. Validate and merge only approved metadata fields.
    """

    original_query = query.strip()
    rule_query, rule_hard_filters = _parse_with_rules(
        original_query
    )
    llm_query, llm_hard_filters, llm_soft_filters = _parse_with_llm(
        original_query
    )

    merged_hard_filters = dict(llm_hard_filters)
    merged_hard_filters.update(rule_hard_filters)
    merged_hard_filters = _normalize_filters(
        merged_hard_filters
    )

    normalized_soft_filters = _normalize_soft_filters(
        _derive_soft_filters(
            original_query,
            merged_hard_filters,
            llm_soft_filters
        )
    )

    cleaned_query = (
        rule_query
        if rule_query and rule_query != original_query
        else llm_query
    )
    cleaned_query = cleaned_query or original_query

    print("Parsed Query:", cleaned_query)
    print("Parsed Hard Filters:", merged_hard_filters)
    print("Parsed Soft Filters:", normalized_soft_filters)

    return QueryParseResult(
        cleaned_query=cleaned_query,
        hard_filters=merged_hard_filters,
        soft_filters=normalized_soft_filters
    )


def _parse_with_rules(
    query: str
) -> tuple[str, dict[str, Any]]:
    lowered_query = query.lower()
    metadata_filters: dict[str, Any] = {}

    if "jira" in lowered_query:
        metadata_filters["source_type"] = "jira"

    if "confluence" in lowered_query:
        metadata_filters["source_type"] = "confluence"

    if "pdf" in lowered_query:
        metadata_filters["source_type"] = "pdf"

    for pattern, status in STATUS_PATTERNS.items():
        if pattern in lowered_query:
            metadata_filters["status"] = status
            break

    for pattern, issue_type in ISSUE_TYPE_PATTERNS.items():
        if re.search(
            rf"\b{re.escape(pattern)}s?\b",
            lowered_query
        ):
            metadata_filters["issue_type"] = issue_type
            break

    ticket_match = re.search(
        r"\b([A-Z][A-Z0-9]+-\d+)\b",
        query
    )
    if ticket_match:
        metadata_filters["source"] = ticket_match.group(1)

    if "status" in lowered_query:
        metadata_filters["section_type"] = "status"
    elif "summary" in lowered_query:
        metadata_filters["section_type"] = "summary"
    elif "description" in lowered_query:
        metadata_filters["section_type"] = "description"

    page_match = re.search(
        r"\bpage\s+(\d+)\b",
        lowered_query
    )
    if page_match:
        metadata_filters["page"] = int(
            page_match.group(1)
        )

    project_match = re.search(
        r"\bproject\s+([a-zA-Z0-9_-]+)\b",
        query,
        flags=re.IGNORECASE
    )
    if project_match:
        metadata_filters["project"] = (
            project_match.group(1)
        )

    preferred_source_type = metadata_filters.get(
        "source_type"
    )
    resolved_entity, _matched_source_types = (
        resolve_query_entity(
            query,
            preferred_source_type=preferred_source_type,
        )
    )

    if resolved_entity is not None:
        metadata_filters["source"] = (
            resolved_entity.source_id
        )
        metadata_filters.setdefault(
            "source_type",
            resolved_entity.source_type
        )

    cleaned_query = _remove_filter_terms(query)
    return cleaned_query or query, metadata_filters


def _parse_with_llm(
    query: str
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    client = _get_anthropic_client()
    if client is None:
        return query, {}, {}

    prompt = f"""
You are a query understanding system for retrieval over Jira, Confluence, and PDF chunks.

Extract:
1. a cleaned semantic query suitable for BM25/vector retrieval
2. hard_filters only when the query strongly and explicitly implies them
3. soft_filters when the query suggests likely candidate scopes for retrieval

Allowed metadata keys:
- source_type
- source
- status
- issue_type
- page
- project
- parent_key
- parent_title
- section_type
- title
- document
- h1
- h2
- h3

Allowed source_type values:
- jira
- confluence
- pdf

Rules:
- Return JSON only.
- Do not invent metadata that is not clearly implied by the query.
- Keep cleaned_query concise and meaningful.
- If unsure, leave hard_filters empty.
- soft_filters may include likely candidate source_type values when semantically appropriate.
- For Jira ticket ids like SCRUM-12, use source.
- For page references like "page 4", use page as an integer.
- Normalize likely statuses to values like Done, In Progress, Open, To Do.
- Normalize likely issue types to values like Bug, Task, Story, Epic.
- Prefer soft source_type hints for broad topical queries like password reset, architecture, runbook, policy, recovery.

Return exactly this shape:
{{
  "cleaned_query": "string",
  "hard_filters": {{
    "key": "value"
  }},
  "soft_filters": {{
    "key": "value"
  }}
}}

User query:
{query}
""".strip()

    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=300,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        content = response.content[0].text.strip()
        payload = _extract_json_object(content)
        if not payload:
            return query, {}, {}

        cleaned_query = payload.get(
            "cleaned_query",
            query
        )
        hard_filters = payload.get(
            "hard_filters",
            {}
        )
        soft_filters = payload.get(
            "soft_filters",
            {}
        )

        if not isinstance(cleaned_query, str):
            cleaned_query = query
        if not isinstance(hard_filters, dict):
            hard_filters = {}
        if not isinstance(soft_filters, dict):
            soft_filters = {}

        return (
            cleaned_query.strip() or query,
            hard_filters,
            soft_filters
        )
    except Exception as exc:
        print("LLM query parser fallback:", exc)
        return query, {}, {}


def _derive_soft_filters(
    query: str,
    hard_filters: dict[str, Any],
    llm_soft_filters: dict[str, Any]
) -> dict[str, Any]:
    if hard_filters:
        return {}

    resolved_entity, matched_source_types = (
        resolve_query_entity(query)
    )

    if resolved_entity is not None:
        return {
            "source_type": [
                resolved_entity.source_type
            ]
        }

    if len(matched_source_types) > 1:
        return {
            "source_type": matched_source_types
        }

    return llm_soft_filters


def _extract_json_object(
    raw_text: str
) -> dict[str, Any] | None:
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(
        r"\{.*\}",
        raw_text,
        flags=re.DOTALL
    )
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        return None

    return None


def _normalize_filters(
    metadata_filters: dict[str, Any]
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}

    for key, value in metadata_filters.items():
        if key not in ALLOWED_FILTER_KEYS:
            continue

        normalized_value = _normalize_filter_value(
            key,
            value
        )
        if normalized_value is None:
            continue

        normalized[key] = normalized_value

    return normalized


def _normalize_soft_filters(
    metadata_filters: dict[str, Any]
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}

    for key, value in metadata_filters.items():
        if key not in ALLOWED_FILTER_KEYS:
            continue

        if isinstance(value, list):
            normalized_values = []
            for item in value:
                normalized_item = _normalize_filter_value(
                    key,
                    item
                )
                if normalized_item is not None:
                    normalized_values.append(
                        normalized_item
                    )
            if normalized_values:
                normalized[key] = normalized_values
            continue

        normalized_value = _normalize_filter_value(
            key,
            value
        )
        if normalized_value is not None:
            normalized[key] = normalized_value

    return normalized


def _normalize_filter_value(
    key: str,
    value: Any
) -> Any | None:
    if value is None:
        return None

    if isinstance(value, list):
        normalized_values = []
        for item in value:
            normalized_item = _normalize_filter_value(
                key,
                item
            )
            if normalized_item is None:
                continue
            if isinstance(normalized_item, list):
                normalized_values.extend(
                    normalized_item
                )
            else:
                normalized_values.append(
                    normalized_item
                )
        deduped_values = []
        for item in normalized_values:
            if item not in deduped_values:
                deduped_values.append(item)
        return deduped_values or None

    if key == "page":
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    if key == "source_type":
        normalized = str(value).strip().lower()
        if normalized in SOURCE_TYPE_VALUES:
            return normalized
        return None

    if key == "status":
        lowered = str(value).strip().lower()
        return STATUS_PATTERNS.get(
            lowered,
            str(value).strip()
        )

    if key == "issue_type":
        lowered = str(value).strip().lower()
        return ISSUE_TYPE_PATTERNS.get(
            lowered,
            str(value).strip().title()
        )

    return str(value).strip() or None


def _remove_filter_terms(query: str) -> str:
    cleaned = query

    removable_patterns = [
        r"\bjira\b",
        r"\bconfluence\b",
        r"\bpdf\b",
        r"\bdone\b",
        r"\bclosed\b",
        r"\bresolved\b",
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
        r"\bproject\s+[a-zA-Z0-9_-]+\b",
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
        r"\b(in|from|on|for|about|within)\s*([?.!,])",
        r"\2",
        cleaned,
        flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\b(in|from|on|for|about|within)\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned
    ).strip(" ,.-")

    return cleaned
