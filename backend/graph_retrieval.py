from graph_context import get_graph_context
from source_retriever import retrieve_by_source


def build_graph_context(
    source_id: str,
    source_type: str
):

    graph_context = get_graph_context(
        source_id,
        source_type
    )

    parent_chunks = []
    child_chunks = []
    linked_chunks = []

    parent_citations = []
    child_citations = []
    linked_citations = []

    seen_parents = set()
    seen_children = set()
    seen_linked = set()

    # ====================
    # Parent Retrieval
    # ====================

    for parent_id in graph_context["parent_ids"]:

        if parent_id in seen_parents:
            continue

        seen_parents.add(parent_id)

        result = retrieve_by_source(
            parent_id
        )

        parent_chunks.extend(
            result["documents"]
        )

        parent_citations.append(
            parent_id
        )

    # ====================
    # Child Retrieval
    # ====================

    for child_id in graph_context["child_ids"]:

        if child_id in seen_children:
            continue

        seen_children.add(child_id)

        result = retrieve_by_source(
            child_id
        )

        child_chunks.extend(
            result["documents"]
        )

        child_citations.append(
            child_id
        )

    # ====================
    # Linked Retrieval
    # (Cross-system: Jira ↔ Confluence)
    # ====================

    for linked_id in graph_context.get(
        "linked_ids", []
    ):

        if linked_id in seen_linked:
            continue

        seen_linked.add(linked_id)

        result = retrieve_by_source(
            linked_id
        )

        linked_chunks.extend(
            result["documents"]
        )

        linked_citations.append(
            linked_id
        )

    return {

        "parent_chunks": parent_chunks,

        "child_chunks": child_chunks,

        "linked_chunks": linked_chunks,

        "parent_citations": parent_citations,

        "child_citations": child_citations,

        "linked_citations": linked_citations

    }


if __name__ == "__main__":

    result = build_graph_context(
        "GENAI-1",
        "jira"
    )

    print("\nPARENT CHUNKS")
    print("=" * 50)

    for chunk in result["parent_chunks"]:
        print(chunk)

    print("\nCHILD CHUNKS")
    print("=" * 50)

    for chunk in result["child_chunks"]:
        print(chunk)

    print("\nLINKED CHUNKS")
    print("=" * 50)

    for chunk in result["linked_citations"]:
        print(chunk)