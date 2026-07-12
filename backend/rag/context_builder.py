def build_context(
    primary_chunks,
    parent_chunks=None,
    child_chunks=None,
    linked_chunks=None
):

    parent_chunks = parent_chunks or []
    child_chunks = child_chunks or []
    linked_chunks = linked_chunks or []

    sections = []

    # ====================
    # Primary Context
    # ====================

    if primary_chunks:

        sections.append(
            "PRIMARY CONTEXT\n"
            "================\n"
        )

        for chunk in primary_chunks:

            sections.append(chunk)
            sections.append("\n")

    # ====================
    # Parent Context
    # ====================

    if parent_chunks:

        sections.append(
            "\nRELATED PARENT CONTEXT\n"
            "======================\n"
        )

        for chunk in parent_chunks:

            sections.append(chunk)
            sections.append("\n")

    # ====================
    # Child Context
    # ====================

    if child_chunks:

        sections.append(
            "\nRELATED CHILD CONTEXT\n"
            "=====================\n"
        )

        for chunk in child_chunks:

            sections.append(chunk)
            sections.append("\n")

        for chunk in linked_chunks:
            sections.append(chunk)
            sections.append("\n")

    return "\n".join(sections)


if __name__ == "__main__":

    primary = [
        "Password Reset Feature"
    ]

    parents = [
        "Authentication & Security"
    ]

    children = [
        "Token Generation & Emailing"
    ]

    context = build_context(
        primary,
        parents,
        children
    )

    print(context)