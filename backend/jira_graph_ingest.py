import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from connectors.jira_loader import load_jira

load_dotenv()


def create_jira_graph(session, issues):
    board_key = os.getenv("JIRA_PROJECT_KEY") or os.getenv("JIRA_SPACE") or os.getenv("JIRA_PROJECT") or "GENAI"

    session.run(
        """
        MERGE (board:JiraBoard {key: $board_key})
        SET board.name = $board_key
        """,
        board_key=board_key,
    )

    for issue in issues:
        issue_key = issue["key"]
        fields = issue["fields"]
        summary = fields.get("summary", "")
        issue_type = fields.get("issuetype", {}).get("name", "")
        parent = fields.get("parent")

        session.run(
            """
            MERGE (n:Jira {
                key: $key
            })
            SET n.summary = $summary,
                n.issue_type = $issue_type,
                n.display = $display
            MERGE (board:JiraBoard {key: $board_key})
            MERGE (board)-[:CONTAINS]->(n)
            """,
            key=issue_key,
            summary=summary,
            issue_type=issue_type,
            display=issue_key,
            board_key=board_key,
        )

        if not parent:
            continue

        parent_key = parent["key"]
        relation = "HAS_CHILD" if issue_type.lower() == "subtask" else "HAS_TICKET"

        session.run(
            f"""
            MERGE (parent:Jira {{key: $parent_key}})
            MERGE (child:Jira {{key: $child_key}})
            MERGE (parent)-[:{relation}]->(child)
            """,
            parent_key=parent_key,
            child_key=issue_key,
        )


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
        with driver.session() as session:
            create_jira_graph(session, issues)
    finally:
        driver.close()


if __name__ == "__main__":
    main()


