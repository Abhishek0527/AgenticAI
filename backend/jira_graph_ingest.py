from neo4j import GraphDatabase
from dotenv import load_dotenv
from connectors.jira_loader import load_jira
import os

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD")
    )
)

issues = load_jira()

with driver.session() as session:

    for issue in issues:

        parent = issue["fields"].get("parent")

        if not parent:
            continue

        parent_key = parent["key"]
        child_key = issue["key"]

        issue_type = issue["fields"]["issuetype"]["name"]

        if issue_type.lower() == "subtask":

            relationship = "HAS_CHILD"

        else:

            relationship = "HAS_TICKET"

        query = f"""
        MATCH (parent:Jira {{
            key: $parent_key
        }})

        MATCH (child:Jira {{
            key: $child_key
        }})

        MERGE (parent)-[:{relationship}]->(child)
        """

        session.run(
            query,
            parent_key=parent_key,
            child_key=child_key
        )


