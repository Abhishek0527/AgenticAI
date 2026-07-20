import re


PARENT_NOISE_PATTERNS = (
    "In a sentence or two, describe the purpose of this space.",
    "These are all the labels in use in this space.",
    "This list below will automatically update each time somebody in your space creates or updates content.",
)


def build_context(
    primary_chunks,
    parent_chunks=None,
    child_chunks=None,
    linked_chunks=None,
    semantic_linked_chunks=None
):

    parent_chunks = parent_chunks or []
    child_chunks = child_chunks or []
    linked_chunks = linked_chunks or []
    semantic_linked_chunks = semantic_linked_chunks or []

    sections = []

    def add_section(
        title: str,
        chunks: list[str],
        drop_noise: bool = False
    ) -> None:
        cleaned_chunks = []
        seen_chunks = set()
        for chunk in chunks:
            cleaned_chunk = _clean_chunk_text(
                chunk
            )
            normalized_chunk = " ".join(
                cleaned_chunk.split()
            ).strip()
            if not normalized_chunk:
                continue
            if (
                drop_noise
                and any(
                    noise in cleaned_chunk
                    for noise in PARENT_NOISE_PATTERNS
                )
            ):
                continue
            if normalized_chunk in seen_chunks:
                continue
            seen_chunks.add(normalized_chunk)
            cleaned_chunks.append(cleaned_chunk)

        if not cleaned_chunks:
            return

        sections.append(title)

        for chunk in cleaned_chunks:
            sections.append(chunk)
            sections.append("\n")

    # ====================
    # Primary Context
    # ====================

    if primary_chunks:
        add_section(
            "PRIMARY CONTEXT\n"
            "================\n",
            primary_chunks
        )

    # ====================
    # Parent Context
    # ====================

    if parent_chunks:
        add_section(
            "\nRELATED PARENT CONTEXT\n"
            "======================\n",
            parent_chunks,
            drop_noise=True
        )

    # ====================
    # Child Context
    # ====================

    if child_chunks:
        add_section(
            "\nRELATED CHILD CONTEXT\n"
            "=====================\n",
            child_chunks
        )

    if linked_chunks:
        add_section(
            "\nRELATED LINKED CONTEXT\n"
            "======================\n",
            linked_chunks
        )

    if semantic_linked_chunks:
        add_section(
            "\nSEMANTICALLY RELATED CONTEXT\n"
            "============================\n",
            semantic_linked_chunks
        )

    return "\n".join(sections)


def _clean_chunk_text(chunk: str) -> str:
    cleaned = chunk.replace(
        "â†“",
        " -> "
    ).replace(
        "â€™",
        "'"
    )

    cleaned = re.sub(
        r"\b([^\n.]{2,}?)\s+\1\b",
        r"\1",
        cleaned,
        flags=re.IGNORECASE
    )

    lines = []
    seen_lines = set()
    for raw_line in cleaned.splitlines():
        line = " ".join(
            raw_line.split()
        ).strip()
        if not line:
            continue
        if line in seen_lines:
            continue
        seen_lines.add(line)
        lines.append(line)

    cleaned = "\n".join(lines).strip()
    return cleaned


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
