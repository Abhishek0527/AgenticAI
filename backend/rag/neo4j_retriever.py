import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import DriverError, ServiceUnavailable
from rag.embedding import embed_query

load_dotenv()

# ---------------------------------------------------------------------------
# Lazy singleton driver
# ---------------------------------------------------------------------------
_driver = None
_neo4j_enabled = False


def _get_driver():
    global _driver, _neo4j_enabled

    if _driver is not None:
        return _driver

    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        _driver = driver
        _neo4j_enabled = True
        print(f"Neo4jRetriever: Connected to Neo4j at {uri}")
    except (ServiceUnavailable, DriverError) as e:
        print(f"Neo4jRetriever: Could not connect to Neo4j – graph retrieval disabled. ({e})")
        _neo4j_enabled = False

    return _driver


def _run_query(query: str, parameters: dict = None):
    driver = _get_driver()
    if driver is None:
        return []
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    try:
        with driver.session(database=database) as session:
            result = session.run(query, parameters or {})
            return list(result)
    except Exception as e:
        print(f"Neo4jRetriever Query Error: {e}")
        return []


# ---------------------------------------------------------------------------
# Public retrieval function
# ---------------------------------------------------------------------------

def neo4j_retrieve(query: str, source: str, top_k: int = 10) -> list[str]:
    """
    Retrieve relevant text chunks from Neo4j.

    Strategy
    --------
    1. **Keyword / fulltext search** on Chunk.text (always runs).
    2. **Enrichment** – for each matched chunk, also fetch the parent Issue's
       summary + description so the LLM gets richer context.
    3. Falls back gracefully if Neo4j is unavailable.
    """
    driver = _get_driver()
    if not _neo4j_enabled or driver is None:
        return []

    source_filter = _build_source_filter(source)
    results: list[str] = []

    # ------------------------------------------------------------------
    # 1. Fulltext / CONTAINS search on Chunk nodes linked to an Issue
    # ------------------------------------------------------------------
    keywords = _extract_keywords(query)
    if keywords and source in ("jira", "all"):
        chunk_query = """
        MATCH (i:Issue)-[:HAS_CHUNK]->(c:Chunk)
        WHERE """ + source_filter + """
        AND any(kw IN $keywords WHERE toLower(c.text) CONTAINS toLower(kw))
        RETURN c.text AS text
        LIMIT $top_k
        """
        rows = _run_query(chunk_query, {"keywords": keywords, "top_k": top_k})
        for row in rows:
            text = row.get("text") or row["text"]
            if text and text not in results:
                results.append(text)

    # ------------------------------------------------------------------
    # 2. Keyword search on Issue summary / description
    # ------------------------------------------------------------------
    if keywords and source in ("jira", "all"):
        issue_query = """
        MATCH (i:Issue)
        WHERE """ + source_filter + """
        AND any(kw IN $keywords WHERE
            toLower(i.summary)     CONTAINS toLower(kw)
            OR toLower(i.description) CONTAINS toLower(kw)
        )
        RETURN i.key + ': ' + i.summary + '. ' + coalesce(i.description, '') AS text
        LIMIT $top_k
        """
        rows = _run_query(issue_query, {"keywords": keywords, "top_k": top_k})
        for row in rows:
            text = row.get("text") or row["text"]
            if text and text not in results:
                results.append(text)

    # ------------------------------------------------------------------
    # 3. Relationship-aware context: issues related to matched issues
    # ------------------------------------------------------------------
    if results and source in ("jira", "all"):
        related_query = """
        MATCH (i:Issue)-[r]->(related:Issue)
        WHERE """ + source_filter + """
        AND any(kw IN $keywords WHERE
            toLower(i.summary) CONTAINS toLower(kw)
        )
        RETURN related.key + ': ' + related.summary + '. ' + coalesce(related.description, '') AS text
        LIMIT $top_k
        """
        rows = _run_query(related_query, {"keywords": keywords, "top_k": top_k})
        for row in rows:
            text = row.get("text") or row["text"]
            if text and text not in results:
                results.append(text)

    print(f"Neo4jRetriever: source={source!r}, keywords={keywords}, chunks_returned={len(results)}")
    return results[:top_k]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_source_filter(source: str) -> str:
    """Return Cypher WHERE clause fragment for source filtering on Issue nodes."""
    if source == "jira":
        return 'i.source_type = "jira"'
    elif source == "confluence":
        return 'i.source_type = "confluence"'
    else:
        # Generic / unknown source – no filter, search everything
        return "true"


def _extract_keywords(query: str, max_words: int = 8) -> list[str]:
    """
    Simple keyword extractor: strips stop-words and returns the most
    meaningful tokens.  No external NLP dependency required.
    """
    STOP_WORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "shall", "can",
        "to", "of", "in", "on", "at", "by", "for", "with", "from",
        "and", "or", "but", "not", "what", "how", "why", "when",
        "where", "who", "which", "that", "this", "it", "its",
        "me", "my", "we", "our", "you", "your", "he", "she", "they",
        "their", "i", "all", "any", "about", "tell", "give", "show",
    }
    tokens = query.lower().split()
    keywords = [t.strip("?.!,;:\"'") for t in tokens if t not in STOP_WORDS and len(t) > 2]
    return keywords[:max_words]
