import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from connectors.confluence_loader import load_confluence_pages
from connectors.jira_loader import load_jira
from graph_linker import link_jira_and_confluence

load_dotenv()


def main():
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(
            os.getenv("NEO4J_USERNAME"),
            os.getenv("NEO4J_PASSWORD"),
        ),
    )

    try:
        issues = load_jira()
        pages = load_confluence_pages()

        with driver.session() as session:
            link_jira_and_confluence(session, issues, pages)

        print(f"Linked {len(issues)} Jira issues with {len(pages)} Confluence pages")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
