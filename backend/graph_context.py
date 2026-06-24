from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()


def get_graph_context(source_id, source_type):

    context = {
        "parents": [],
        "children": []
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



            if source_type == "jira":

                parent_result = session.run(
                    """
                    MATCH (parent:Jira)-[]->(child:Jira {
                        key:$source_id
                    })

                    RETURN parent.title as title
                    """,
                    source_id=source_id
                )

                for row in parent_result:

                    context["parents"].append(
                        row["title"]
                    )

                child_result = session.run(
                    """
                    MATCH (parent:Jira {
                        key:$source_id
                    })-[]->(child:Jira)

                    RETURN child.title as title
                    """,
                    source_id=source_id
                )

                for row in child_result:

                    context["children"].append(
                        row["title"]
                    )

           

            elif source_type == "confluence":

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

                    context["parents"].append(
                        row["title"]
                    )

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

                    context["children"].append(
                        row["title"]
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

    print(
        get_graph_context(
            "SCRUM-7",
            "jira"
        )
    )

    print(
        get_graph_context(
            "Password Reset Design",
            "confluence"
        )
    )