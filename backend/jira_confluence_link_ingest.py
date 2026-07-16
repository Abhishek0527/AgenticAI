"""
Jira ↔ Confluence Cross-Link Ingestion
---------------------------------------
Creates relationships between EXISTING Jira and
Confluence nodes in Neo4j. No new nodes are created.

Direction 1:
  Jira description → Confluence page URL/title
  Relationship: (Jira)-[:REFERENCES_DOC]->(Confluence)

Direction 2:
  Confluence page text → Jira ticket keys
  Relationship: (Confluence)-[:MENTIONS_TICKET]->(Jira)
"""

import re
import os
import requests

from neo4j import GraphDatabase
from dotenv import load_dotenv

from connectors.jira_loader import load_jira, extract_text
from connectors.confluence_loader import load_confluence_pages

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD")
    )
)


# ============================================
# HELPERS
# ============================================

def extract_confluence_titles_from_jira(issue, confluence_titles):
    """
    Scan a Jira issue's description for references
    to Confluence page titles or Confluence URLs.
    Returns a set of matched Confluence titles.
    """

    matched = set()

    # Get raw description text

    description = issue["fields"].get("description")

    if not description:
        return matched

    desc_text = "\n".join(extract_text(description))

    if not desc_text.strip():
        return matched

    # --- Match Confluence page titles ---

    lower_text = desc_text.lower()

    for title in confluence_titles:

        if title.lower() in lower_text:
            matched.add(title)

    # --- Match Confluence URLs ---
    # Pattern: https://<domain>/wiki/spaces/<space>/pages/<id>/<title>

    confluence_url = os.getenv(
        "CONFLUENCE_URL",
        ""
    ).rstrip("/")

    url_pattern = re.compile(
        re.escape(confluence_url)
        + r"/wiki/spaces/\w+/pages/\d+/([^\s\)\"'\]]+)",
        re.IGNORECASE
    )

    for match in url_pattern.finditer(desc_text):

        url_slug = match.group(1)

        # URL slugs use + or %20 for spaces
        decoded_slug = (
            url_slug
            .replace("+", " ")
            .replace("%20", " ")
        )

        for title in confluence_titles:

            if title.lower() == decoded_slug.lower():
                matched.add(title)

    return matched


def fetch_jira_remote_confluence_links(
    issue_key, confluence_titles
):
    """
    Call Jira Remote Links API for a ticket and
    match any linked Confluence pages against
    existing Confluence node titles.
    Returns a set of matched Confluence titles.
    """

    matched = set()

    email = os.getenv("ATLASSIAN_EMAIL")
    token = os.getenv("ATLASSIAN_API_TOKEN")
    base_url = os.getenv(
        "ATLASSIAN_BASE_URL", ""
    ).rstrip("/")

    if not all([email, token, base_url]):
        return matched

    url = (
        f"{base_url}/rest/api/3/issue"
        f"/{issue_key}/remotelink"
    )

    try:

        response = requests.get(
            url,
            auth=(email, token)
        )

        response.raise_for_status()

        remote_links = response.json()

        for link in remote_links:

            link_url = (
                link.get("object", {})
                .get("url", "")
            )

            link_title = (
                link.get("object", {})
                .get("title", "")
            )

            # Match by title
            for title in confluence_titles:

                if (
                    title.lower()
                    == link_title.lower()
                ):
                    matched.add(title)

                # Match by URL containing
                # the page title slug
                elif title.lower().replace(
                    " ", "+"
                ) in link_url.lower():
                    matched.add(title)

                elif title.lower().replace(
                    " ", "%20"
                ) in link_url.lower():
                    matched.add(title)

    except Exception as e:

        print(
            f"  Warning: Could not fetch "
            f"remote links for {issue_key}: {e}"
        )

    return matched


def extract_jira_keys_from_confluence(page, jira_keys):
    """
    Scan a Confluence page's text content for
    Jira ticket keys (e.g. GENAI-5, SCRUM-12).
    Returns a set of matched Jira keys.
    """

    matched = set()

    text = page.get("text", "")

    if not text.strip():
        return matched

    # Match ticket keys like GENAI-123, SCRUM-7

    key_pattern = re.compile(
        r"\b([A-Z][A-Z0-9]+-\d+)\b"
    )

    found_keys = set(
        key_pattern.findall(text)
    )

    for key in found_keys:

        if key in jira_keys:
            matched.add(key)

    return matched


# ============================================
# LOAD DATA
# ============================================

print("\n=== Loading Jira Issues ===")
issues = load_jira()
print(f"Loaded {len(issues)} Jira issues")

print("\n=== Loading Confluence Pages ===")
pages = load_confluence_pages()
print(f"Loaded {len(pages)} Confluence pages")


# Build lookup sets

confluence_titles = set(
    page["title"] for page in pages
)

jira_keys = set(
    issue["key"] for issue in issues
)


# ============================================
# PASS 1 — Jira -> Confluence (REFERENCES_DOC)
# ============================================

print("\n" + "=" * 50)
print("PASS 1: Jira -> Confluence (REFERENCES_DOC)")
print("=" * 50)

link_count = 0

with driver.session() as session:

    for issue in issues:

        issue_key = issue["key"]

        # From description text
        matched_titles = (
            extract_confluence_titles_from_jira(
                issue,
                confluence_titles
            )
        )

        # From Jira remote links API
        remote_titles = (
            fetch_jira_remote_confluence_links(
                issue_key,
                confluence_titles
            )
        )

        matched_titles = matched_titles | remote_titles

        for title in matched_titles:

            print(
                f"  {issue_key} "
                f"-[:REFERENCES_DOC]-> "
                f"{title}"
            )

            session.run(
                """
                MATCH (j:Jira {
                    key: $jira_key
                })

                MATCH (c:Confluence {
                    title: $conf_title
                })

                MERGE (j)-[:REFERENCES_DOC]->(c)
                """,
                jira_key=issue_key,
                conf_title=title
            )

            link_count += 1

print(f"\nCreated {link_count} REFERENCES_DOC links")


# ============================================
# PASS 2 — Confluence -> Jira (MENTIONS_TICKET)
# ============================================

print("\n" + "=" * 50)
print("PASS 2: Confluence -> Jira (MENTIONS_TICKET)")
print("=" * 50)

link_count = 0

with driver.session() as session:

    for page in pages:

        page_title = page["title"]

        matched_keys = (
            extract_jira_keys_from_confluence(
                page,
                jira_keys
            )
        )

        for key in matched_keys:

            print(
                f"  {page_title} "
                f"-[:MENTIONS_TICKET]-> "
                f"{key}"
            )

            session.run(
                """
                MATCH (c:Confluence {
                    title: $conf_title
                })

                MATCH (j:Jira {
                    key: $jira_key
                })

                MERGE (c)-[:MENTIONS_TICKET]->(j)
                """,
                conf_title=page_title,
                jira_key=key
            )

            link_count += 1

print(f"\nCreated {link_count} MENTIONS_TICKET links")


# ============================================
# DONE
# ============================================

driver.close()

print("\nJira <-> Confluence Link Ingestion Complete")
