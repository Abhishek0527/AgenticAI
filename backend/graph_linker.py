import re

from connectors.jira_loader import issue_to_text


def _normalize_text(text):
    if text is None:
        return ""
    return str(text).lower()


def _phrase_in_text(text, phrase):
    if not text or not phrase:
        return False
    text_lower = _normalize_text(text)
    phrase_lower = _normalize_text(phrase)
    return re.search(rf"(?<!\w){re.escape(phrase_lower)}(?!\w)", text_lower) is not None


def _is_short_generic_title(title):
    if not title:
        return False
    normalized = _normalize_text(title).strip()
    return len(normalized) < 4 and " " not in normalized


def _mentions_confluence_page(text, page):
    if not text:
        return False

    title = page.get("title", "")
    if title and not _is_short_generic_title(title):
        if _phrase_in_text(text, title):
            return True

    page_id = page.get("page_id")
    if page_id and str(page_id) in text:
        return True

    return False


def _merge_confluence_node(session, page):
    """MERGE a Confluence node by page_id (preferred) or title."""
    page_id = page.get("page_id")
    page_title = page.get("title")
    params = {
        "page_id": page_id,
        "page_title": page_title,
        "page_key": f"CONFLUENCE-{page_id}" if page_id else None,
        "page_display": page_title or None,
    }
    if page_id:
        session.run(
            """
            MERGE (page:Confluence {page_id: $page_id})
            SET page.title = coalesce(page.title, $page_title),
                page.key = coalesce(page.key, $page_key),
                page.display = coalesce(page.display, $page_display)
            """,
            **params,
        )
    else:
        session.run(
            """
            MERGE (page:Confluence {title: $page_title})
            SET page.page_id = coalesce(page.page_id, $page_id),
                page.key = coalesce(page.key, $page_key),
                page.display = coalesce(page.display, $page_display)
            """,
            **params,
        )


def ensure_graph_nodes(session, issues, pages):
    """Create Jira and Confluence nodes in Neo4j."""
    for issue in issues:
        session.run(
            """
            MERGE (issue:Jira {key: $issue_key})
            SET issue.summary = coalesce(issue.summary, $summary),
                issue.issue_type = coalesce(issue.issue_type, $issue_type)
            """,
            issue_key=issue.get("key"),
            summary=issue.get("fields", {}).get("summary", ""),
            issue_type=issue.get("fields", {}).get("issuetype", {}).get("name", ""),
        )

    for page in pages:
        _merge_confluence_node(session, page)


def _create_reference(session, page, issue_key, rel_type):
    """Create a directional reference between a Confluence page and Jira issue."""
    page_id = page.get("page_id")

    if rel_type == "REFERENCES_JIRA":
        if page_id:
            query = """
                MERGE (page:Confluence {page_id: $page_id})
                MERGE (issue:Jira {key: $issue_key})
                MERGE (page)-[:REFERENCES_JIRA]->(issue)
            """
        else:
            query = """
                MERGE (page:Confluence {title: $page_title})
                MERGE (issue:Jira {key: $issue_key})
                MERGE (page)-[:REFERENCES_JIRA]->(issue)
            """
    else:
        if page_id:
            query = """
                MERGE (issue:Jira {key: $issue_key})
                MERGE (page:Confluence {page_id: $page_id})
                MERGE (issue)-[:REFERENCES_CONFLUENCE]->(page)
            """
        else:
            query = """
                MERGE (issue:Jira {key: $issue_key})
                MERGE (page:Confluence {title: $page_title})
                MERGE (issue)-[:REFERENCES_CONFLUENCE]->(page)
            """

    session.run(
        query,
        page_id=page_id,
        page_title=page.get("title"),
        issue_key=issue_key,
    )


def link_confluence_pages_to_jira(session, pages, issues):
    """Detect Jira issue keys mentioned in Confluence page text."""
    created = set()

    for page in pages:
        page_text = " ".join(
            filter(None, [page.get("title", ""), page.get("text", "")])
        )

        for issue in issues:
            issue_key = issue["key"]

            if not _phrase_in_text(page_text, issue_key):
                continue

            pair = (page.get("title"), issue_key)
            if pair in created:
                continue

            _create_reference(session, page, issue_key, "REFERENCES_JIRA")
            created.add(pair)

    return created


def link_jira_issues_to_confluence(session, issues, pages):
    """Detect Confluence page references in Jira issue descriptions."""
    created = set()

    for issue in issues:
        issue_text = issue_to_text(issue)

        for page in pages:
            if not _mentions_confluence_page(issue_text, page):
                continue

            pair = (issue.get("key"), page.get("title"))
            if pair in created:
                continue

            _create_reference(session, page, issue.get("key"), "REFERENCES_CONFLUENCE")
            created.add(pair)

    return created


def link_jira_and_confluence(session, issues, pages):
    """Main entry point: create nodes and cross-reference links."""
    ensure_graph_nodes(session, issues, pages)
    link_confluence_pages_to_jira(session, pages, issues)
    link_jira_issues_to_confluence(session, issues, pages)
