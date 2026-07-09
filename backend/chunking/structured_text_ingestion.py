from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from .semantic_chunker import SemanticChunker


def _chunk_section_text(
    text: str,
    chunk_size: int = 200,
    overlap: int = 75
) -> list[str]:
    if not text or not text.strip():
        return []

    chunker = SemanticChunker(
        max_chunk_size=chunk_size,
        overlap=overlap
    )

    return chunker._semantic_split(text.strip())


def _normalize_heading_stack(
    current_h1: str | None,
    current_h2: str | None,
    current_h3: str | None,
    level: int,
    text: str
) -> tuple[str | None, str | None, str | None]:
    if level == 1:
        return text, None, None
    if level == 2:
        return current_h1, text, None
    if level == 3:
        return current_h1, current_h2, text
    return current_h1, current_h2, current_h3


def _extract_confluence_sections(
    html: str,
    title: str
) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body or soup

    sections: list[dict] = []
    current_h1 = title
    current_h2 = None
    current_h3 = None
    current_text: list[str] = []

    def flush_section() -> None:
        nonlocal current_text
        text = "\n".join(
            line.strip()
            for line in current_text
            if line and line.strip()
        ).strip()
        if text:
            sections.append(
                {
                    "h1": current_h1,
                    "h2": current_h2,
                    "h3": current_h3,
                    "text": text,
                }
            )
        current_text = []

    for node in body.descendants:
        if not isinstance(node, Tag):
            continue

        if node.name in {"h1", "h2", "h3"}:
            flush_section()
            heading_text = node.get_text(" ", strip=True)
            level = int(node.name[1])
            current_h1, current_h2, current_h3 = _normalize_heading_stack(
                current_h1,
                current_h2,
                current_h3,
                level,
                heading_text
            )
            continue

        if node.name in {"p", "li"}:
            text = node.get_text(" ", strip=True)
            if text:
                current_text.append(text)

    flush_section()

    if not sections:
        fallback_text = BeautifulSoup(
            html,
            "html.parser"
        ).get_text("\n", strip=True)
        sections.append(
            {
                "h1": title,
                "h2": None,
                "h3": None,
                "text": fallback_text,
            }
        )

    return sections


def build_confluence_chunks_with_metadata(
    page: dict,
    chunk_size: int = 200,
    overlap: int = 75
) -> tuple[list[str], list[dict]]:
    title = page["title"]
    parent_title = page.get("parent_title", "")
    html = page.get("html", "")
    page_id = page["page_id"]

    sections = _extract_confluence_sections(
        html,
        title
    )

    chunks: list[str] = []
    metadatas: list[dict] = []

    for section in sections:
        section_chunks = _chunk_section_text(
            section["text"],
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk in section_chunks:
            chunks.append(chunk)
            metadatas.append(
                {
                    "source_type": "confluence",
                    "source": title,
                    "title": title,
                    "document": title,
                    "page_id": page_id,
                    "parent_title": parent_title,
                    "project": "authentication_platform",
                    "h1": section["h1"],
                    "h2": section["h2"],
                    "h3": section["h3"],
                    "section_type": "page_content",
                    "chunk_index": len(chunks) - 1,
                }
            )

    return chunks, metadatas


def build_jira_chunks_with_metadata(
    issue: dict,
    chunk_size: int = 200,
    overlap: int = 75
) -> tuple[list[str], list[dict]]:
    fields = issue["fields"]
    ticket_id = issue["key"]
    title = fields["summary"]
    issue_type = fields["issuetype"]["name"]
    status = fields["status"]["name"]
    parent = fields.get("parent")
    parent_key = parent["key"] if parent else ""

    sections = [
        {
            "section_type": "summary",
            "h1": title,
            "h2": "Summary",
            "h3": None,
            "text": title,
        },
        {
            "section_type": "description",
            "h1": title,
            "h2": "Description",
            "h3": None,
            "text": _extract_jira_description_text(
                fields.get("description")
            ),
        },
        {
            "section_type": "status",
            "h1": title,
            "h2": "Status",
            "h3": None,
            "text": status,
        },
    ]

    chunks: list[str] = []
    metadatas: list[dict] = []

    for section in sections:
        section_chunks = _chunk_section_text(
            section["text"],
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk in section_chunks:
            chunks.append(chunk)
            metadatas.append(
                {
                    "source_type": "jira",
                    "source": ticket_id,
                    "title": title,
                    "document": title,
                    "issue_type": issue_type,
                    "status": status,
                    "parent_key": parent_key,
                    "project": "authentication_platform",
                    "h1": section["h1"],
                    "h2": section["h2"],
                    "h3": section["h3"],
                    "section_type": section["section_type"],
                    "chunk_index": len(chunks) - 1,
                }
            )

    return chunks, metadatas


def _extract_jira_description_text(description: dict | None) -> str:
    if not description:
        return ""

    lines: list[str] = []

    def walk(node: dict | list | str | None) -> None:
        if node is None:
            return

        if isinstance(node, str):
            if node.strip():
                lines.append(node.strip())
            return

        if isinstance(node, list):
            for item in node:
                walk(item)
            return

        if not isinstance(node, dict):
            return

        node_type = node.get("type")

        if node_type == "heading":
            heading_level = node.get("attrs", {}).get("level")
            heading_text = _collect_jira_text(
                node.get("content", [])
            )
            if heading_text:
                lines.append(
                    f"H{heading_level}: {heading_text}"
                )
            return

        if node_type in {"paragraph", "listItem"}:
            paragraph_text = _collect_jira_text(
                node.get("content", [])
            )
            if paragraph_text:
                lines.append(paragraph_text)

        for value in node.values():
            if isinstance(value, (dict, list)):
                walk(value)

    walk(description)

    return "\n".join(lines).strip()


def _collect_jira_text(nodes: list[dict]) -> str:
    parts: list[str] = []

    for node in nodes:
        if not isinstance(node, dict):
            continue

        if node.get("type") == "text":
            text = node.get("text", "").strip()
            if text:
                parts.append(text)
            continue

        content = node.get("content", [])
        if content:
            nested = _collect_jira_text(content)
            if nested:
                parts.append(nested)

    return " ".join(parts).strip()
