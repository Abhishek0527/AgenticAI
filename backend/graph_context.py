from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()


def get_graph_context(source_id, source_type):

    context = {
        "parent_ids": [],
        "child_ids": [],
        "linked_ids": []
    }

    driver = None

    try:

        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(
                os.getenv("NEO4J_USERNAME"),
                os.getenv("NEO4J_PASSWORD")
            )
        )

        with driver.session() as session:

            # ====================
            # Jira Graph
            # ====================

            if source_type == "jira":

                # Parent IDs

                parent_result = session.run(
                    """
                    MATCH (parent:Jira)-[]->(child:Jira {
                        key:$source_id
                    })

                    RETURN parent.key as key
                    """,
                    source_id=source_id
                )

                for row in parent_result:

                    context["parent_ids"].append(
                        row["key"]
                    )

                # Child IDs

                child_result = session.run(
                    """
                    MATCH (parent:Jira {
                        key:$source_id
                    })-[]->(child:Jira)

                    RETURN child.key as key
                    """,
                    source_id=source_id
                )

                for row in child_result:

                    context["child_ids"].append(
                        row["key"]
                    )

                # Linked Confluence pages

                linked_result = session.run(
                    """
                    MATCH (j:Jira {
                        key:$source_id
                    })-[:REFERENCES_DOC]->(c:Confluence)

                    RETURN c.title as title
                    """,
                    source_id=source_id
                )

                for row in linked_result:

                    context["linked_ids"].append(
                        row["title"]
                    )

            # ====================
            # Confluence Graph
            # ====================

            elif source_type == "confluence":

                # Parent IDs
                # Confluence title itself acts as ID

                parent_result = session.run(
                    """
                    MATCH (parent:Confluence)-[]->(child:Confluence {
                        title:$source_id
                    })

                    RETURN parent.title as title
                    """,
                    source_id=source_id
                )

                for row in parent_result:

                    context["parent_ids"].append(
                        row["title"]
                    )

                # Child IDs

                child_result = session.run(
                    """
                    MATCH (parent:Confluence {
                        title:$source_id
                    })-[]->(child:Confluence)

                    RETURN child.title as title
                    """,
                    source_id=source_id
                )

                for row in child_result:

                    context["child_ids"].append(
                        row["title"]
                    )

                # Linked Jira tickets mentioned from
                # inside the Confluence page

                linked_result = session.run(
                    """
                    MATCH (c:Confluence {
                        title:$source_id
                    })-[:MENTIONS_TICKET]->(j:Jira)

                    RETURN j.key as key
                    """,
                    source_id=source_id
                )

                for row in linked_result:

                    context["linked_ids"].append(
                        row["key"]
                    )

                # Linked Jira tickets that explicitly
                # reference this Confluence page

                reverse_linked_result = session.run(
                    """
                    MATCH (j:Jira)-[:REFERENCES_DOC]->(
                        c:Confluence {
                            title:$source_id
                        }
                    )

                    RETURN j.key as key
                    """,
                    source_id=source_id
                )

                for row in reverse_linked_result:

                    context["linked_ids"].append(
                        row["key"]
                    )

    except Exception as e:

        print("\n=== GRAPH ERROR ===")
        print(e)
        print("===================\n")

    finally:

        if driver:
            driver.close()

    return context


if __name__ == "__main__":

    print("\nJIRA TEST")
    print(
        get_graph_context(
            "SCRUM-7",
            "jira"
        )
    )

    print("\nCONFLUENCE TEST")
    print(
        get_graph_context(
            "Password Reset Design",
            "confluence"
        )
    )
