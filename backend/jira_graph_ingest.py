from neo4j import GraphDatabase
from dotenv import load_dotenv
from connectors.jira_loader import load_jira, issue_to_text
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

    base_url = os.getenv("ATLASSIAN_BASE_URL", "https://agenticevo.atlassian.net/").rstrip("/")

    # First pass: Create all Jira nodes
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"]["summary"]
        
        print(f"Creating Node: {key} - {summary}")
        status = issue["fields"]["status"]["name"]
        issue_type = issue["fields"]["issuetype"]["name"]
        url = f"{base_url}/browse/{key}"

        create_node_query = """
        MERGE (j:Jira {key: $key})
        SET j.summary = $summary,
            j.status = $status,
            j.type = $type,
            j.url = $url,
            j.display = $display
        """

        session.run(
            create_node_query,
            key=key,
            summary=summary,
            status=status,
            type=issue_type,
            url=url,
            display=f"{key}: {summary}"
        )

    # Create project node and link top-level tickets

    project_key = os.getenv(
        "JIRA_PROJECT_KEY", "SCRUM"
    )

    session.run(
        """
        MERGE (p:Jira {key: $project_key})
        SET p.type = "Project",
            p.url = $url,
            p.display = $display
        """,
        project_key=project_key,
        url=f"{base_url}/browse/{project_key}",
        display=f"Project: {project_key}"
    )

    for issue in issues:

        parent = issue["fields"].get("parent")

        if parent:
            # Has a parent issue — handled below
            continue

        child_key = issue["key"]

        session.run(
            """
            MATCH (project:Jira {
                key: $project_key
            })

            MATCH (child:Jira {
                key: $child_key
            })

            MERGE (project)-[:BELONGS_TO_PROJECT]->(child)
            """,
            project_key=project_key,
            child_key=child_key
        )

    # Second pass: Create parent-child relationships
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


driver.close()

print("Jira Graph Ingestion Complete")