from __future__ import annotations

import re
from dataclasses import dataclass

import chromadb


COLLECTION_NAME = "knowledge_fabric"
CHROMA_PATH = "./chroma_db"

_cached_candidates: list["EntityCandidate"] | None = None


@dataclass(frozen=True)
class EntityCandidate:
    text: str
    normalized_text: str
    source_id: str
    source_type: str


def resolve_query_entity(
    query: str,
    preferred_source_type: str | None = None
) -> tuple[EntityCandidate | None, list[str]]:
    normalized_query = _normalize_text(query)
    if not normalized_query:
        return None, []

    matches: list[EntityCandidate] = []

    for candidate in _load_candidates():
        if candidate.normalized_text not in normalized_query:
            continue
        if preferred_source_type and (
            candidate.source_type != preferred_source_type
        ):
            continue
        matches.append(candidate)

    if not matches:
        return None, []

    matches.sort(
        key=lambda item: (
            len(item.normalized_text),
            item.source_type == preferred_source_type,
        ),
        reverse=True,
    )

    matched_source_types = []
    for candidate in matches:
        if candidate.source_type not in matched_source_types:
            matched_source_types.append(
                candidate.source_type
            )

    top_candidate = matches[0]

    unique_source_ids = {
        candidate.source_id
        for candidate in matches
        if candidate.normalized_text
        == top_candidate.normalized_text
    }

    if (
        len(unique_source_ids) > 1
        and not preferred_source_type
    ):
        return None, matched_source_types

    return top_candidate, matched_source_types


def _load_candidates() -> list[EntityCandidate]:
    global _cached_candidates

    if _cached_candidates is not None:
        return _cached_candidates

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )
    results = collection.get(
        include=["metadatas"]
    )

    seen = set()
    candidates: list[EntityCandidate] = []

    for metadata in results.get("metadatas", []):
        source_id = str(
            metadata.get("source", "")
        ).strip()
        source_type = str(
            metadata.get("source_type", "")
        ).strip().lower()

        if not source_id or not source_type:
            continue

        for key in (
            "source",
            "title",
            "document",
            "h1",
        ):
            value = str(
                metadata.get(key, "")
            ).strip()
            normalized_value = _normalize_text(
                value
            )
            if not normalized_value:
                continue

            candidate_key = (
                normalized_value,
                source_id,
                source_type,
            )
            if candidate_key in seen:
                continue
            seen.add(candidate_key)

            candidates.append(
                EntityCandidate(
                    text=value,
                    normalized_text=normalized_value,
                    source_id=source_id,
                    source_type=source_type,
                )
            )

    _cached_candidates = candidates
    return candidates


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(
        r"[^a-z0-9\s]+",
        " ",
        lowered
    )
    lowered = re.sub(
        r"\s+",
        " ",
        lowered
    ).strip()
    return lowered
