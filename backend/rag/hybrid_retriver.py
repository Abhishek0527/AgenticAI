from rag.bm25_retriever import bm25_retrieve
from rag.retreiver import retrieve_document


def hybrid_retrieve(
    query,
    source=None,
    metadata_filters: dict | None = None,
    soft_filters: dict | None = None
):
    scopes = _build_scopes(
        source,
        metadata_filters or {},
        soft_filters or {}
    )

    merged_docs = []
    merged_metadata = []

    for scope_source, scope_filters in scopes:

        vector_results = retrieve_document(
            query,
            scope_source,
            metadata_filters=scope_filters
        )

        bm25_results = bm25_retrieve(
            query,
            scope_source,
            metadata_filters=scope_filters
        )

        for doc, metadata in zip(
            vector_results["documents"],
            vector_results["metadatas"]
        ):

            if doc not in merged_docs:

                merged_docs.append(doc)
                merged_metadata.append(metadata)

        for doc, metadata in zip(
            bm25_results["documents"],
            bm25_results["metadatas"]
        ):

            if doc not in merged_docs:

                merged_docs.append(doc)
                merged_metadata.append(metadata)

    return {
        "documents": merged_docs,
        "metadatas": merged_metadata
    }


def _build_scopes(
    source,
    hard_filters: dict,
    soft_filters: dict
):
    scopes = []

    soft_source_types = soft_filters.get(
        "source_type"
    )

    if (
        isinstance(soft_source_types, list)
        and soft_source_types
        and "source_type" not in hard_filters
        and not source
    ):
        for source_type in soft_source_types:
            scope_filters = dict(hard_filters)
            for key, value in soft_filters.items():
                if key == "source_type":
                    continue
                if not isinstance(value, list):
                    scope_filters[key] = value
            scope_filters["source_type"] = source_type
            scopes.append((None, scope_filters))

    if not scopes:
        scopes.append((source, hard_filters))

    print("Retrieval Scopes:", scopes)
    return scopes
