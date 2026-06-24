from neo4j import GraphDatabase
from dotenv import load_dotenv
from connectors.confluence_loader import load_confluence_pages
import os

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD")
    )
)

pages = load_confluence_pages()


# --------------------------
# PASS 1 - CREATE NODES
# --------------------------

with driver.session() as session:

    for page in pages:

        print(
            "Creating Node:",
            page["title"]
        )

        session.run(
            """
            MERGE (n:Confluence {
                title: $title
            })
            """,
            title=page["title"]
        )


# --------------------------
# PASS 2 - CREATE RELATIONSHIPS
# --------------------------

with driver.session() as session:

    for page in pages:

        parent_title = page["parent_title"]

        if not parent_title:
            continue

        child_title = page["title"]

        print(
            f"{parent_title} -> {child_title}"
        )

        session.run(
            """
            MATCH (parent:Confluence {
                title: $parent_title
            })

            MATCH (child:Confluence {
                title: $child_title
            })

            MERGE (parent)-[:HAS_PAGE]->(child)
            """,
            parent_title=parent_title,
            child_title=child_title
        )


driver.close()

print("\nConfluence Graph Ingestion Complete")