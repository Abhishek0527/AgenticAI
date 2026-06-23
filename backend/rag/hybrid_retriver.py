from rag.bm25_retriever import bm25_retrieve
from rag.retreiver import retrieve_document
from rag.neo4j_retriever import neo4j_retrieve


def hybrid_retrieve(query, source):
    """Merge results from vector (Chroma), BM25, and Neo4j graph retrieval."""

    vector_results = retrieve_document(query, source) or []
    bm25_results = bm25_retrieve(query, source) or []
    graph_results = neo4j_retrieve(query, source) or []

    merged = []

    # Order: vector > BM25 > graph  (priority by retrieval quality)
    for doc in vector_results + bm25_results + graph_results:
        if doc not in merged:
            merged.append(doc)

    return merged