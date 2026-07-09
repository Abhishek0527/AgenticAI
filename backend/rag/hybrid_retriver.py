from rag.bm25_retriever import bm25_retrieve
from rag.retreiver import retrieve_document


def hybrid_retrieve(
    query,
    source=None,
    metadata_filters: dict | None = None
):

    vector_results = retrieve_document(
        query,
        source,
        metadata_filters=metadata_filters
    )

    bm25_results = bm25_retrieve(
        query,
        source,
        metadata_filters=metadata_filters
    )

    merged_docs = []
    merged_metadata = []

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
