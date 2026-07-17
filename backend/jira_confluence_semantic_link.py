from connectors.confluence_loader import load_confluence_pages
from connectors.jira_loader import load_jira, issue_to_text
from neo4j import GraphDatabase
from dotenv import load_dotenv
from rag.embedding import embed_query
import numpy as np
import os

load_dotenv()


# ============================================
# LOAD DATA
# ============================================

print("\n=== Loading Jira Issues ===")
issues = load_jira()
print(f"Loaded {len(issues)} Jira issues")

print("\n=== Loading Confluence Pages ===")
pages = load_confluence_pages()
print(f"Loaded {len(pages)} Confluence pages")


# Initialize Neo4j from environment variables
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD")
    )
)


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# Pre-compute Confluence embeddings
print("Embedding Confluence pages...")
for c in pages:
    c_text = c["title"] + " " + c["text"]
    c["embedding"] = embed_query(c_text)

# Pre-compute Jira embeddings
print("Embedding Jira issues...")
for j in issues:
    j_text = j["fields"]["summary"] + " " + issue_to_text(j)
    j["embedding"] = embed_query(j_text)

print("Computing semantic links...")
# Batch ingestion using real data
with driver.session() as session:
    for c in pages:
        c_emb = c["embedding"]

        for j in issues:
            j_emb = j["embedding"]

            score = cosine_similarity(c_emb, j_emb)

            if score > 0.50:
                print("Matched:", c["title"], j["key"])
                session.run(
                    """
                    MATCH (c:Confluence {key: $ckey})
                    MATCH (j:Jira {key: $jid})
                    MERGE (c)-[:RELATES_TO {semantic_score: $score}]->(j)
                    """,
                    ckey=c.get("page_id"),
                    jid=j.get("key"),
                    score=float(score),
                )

driver.close()

print("Semantic Link Ingestion Complete")