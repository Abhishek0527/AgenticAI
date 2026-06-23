import os
from dotenv import load_dotenv
from rag.graphstore import GraphStore

load_dotenv()


def test_graph_db():
    print("=" * 60)
    print("Neo4j Graph Database Verification Script")
    print("=" * 60)

    graph_store = GraphStore()
    
    if not graph_store.enabled:
        print("Error: GraphStore connection is not enabled. Please check Neo4j status and credentials.")
        return

    try:
        # Count Issues
        res = graph_store.execute_query("MATCH (i:Issue) RETURN count(i) AS count")
        issue_count = res[0]["count"] if res else 0
        print(f"Total Issue nodes: {issue_count}")

        # Count Projects
        res = graph_store.execute_query("MATCH (p:Project) RETURN count(p) AS count")
        project_count = res[0]["count"] if res else 0
        print(f"Total Project nodes: {project_count}")

        # Count Users
        res = graph_store.execute_query("MATCH (u:User) RETURN count(u) AS count")
        user_count = res[0]["count"] if res else 0
        print(f"Total User nodes: {user_count}")

        # Count Chunks
        res = graph_store.execute_query("MATCH (c:Chunk) RETURN count(c) AS count")
        chunk_count = res[0]["count"] if res else 0
        print(f"Total Chunk nodes: {chunk_count}")

        # Count Relationships by Type
        print("\nRelationships in Database:")
        res = graph_store.execute_query("""
        MATCH ()-[r]->() 
        RETURN type(r) AS type, count(r) AS count
        ORDER BY count DESC
        """)
        if res:
            for record in res:
                print(f"  - [:{record['type']}] : {record['count']}")
        else:
            print("  No relationships found.")

        # Sample Issues with Assignees & Projects
        print("\nSample Issues in Database:")
        res = graph_store.execute_query("""
        MATCH (i:Issue)
        OPTIONAL MATCH (i)-[:BELONGS_TO]->(p:Project)
        OPTIONAL MATCH (i)-[:ASSIGNED_TO]->(u:User)
        RETURN i.key AS key, i.summary AS summary, i.status AS status, i.type AS type, 
               p.key AS project, u.name AS assignee
        LIMIT 5
        """)
        if res:
            for record in res:
                print(f"  * {record['key']} [{record['type']}]: {record['summary']} ({record['status']})")
                print(f"    Project: {record['project']} | Assignee: {record['assignee']}")
        else:
            print("  No issues found.")

        # Sample Links / Relationships
        print("\nSample Issue-to-Issue Link Relationships:")
        res = graph_store.execute_query("""
        MATCH (a:Issue)-[r]->(b:Issue)
        RETURN a.key AS from_key, type(r) AS type, b.key AS to_key
        LIMIT 5
        """)
        if res:
            for record in res:
                print(f"  * ({record['from_key']}) -[:{record['type']}]-> ({record['to_key']})")
        else:
            print("  No issue-to-issue relationships found.")

        # Sample Chunk-to-Issue Links
        print("\nSample Chunk Links:")
        res = graph_store.execute_query("""
        MATCH (i:Issue)-[r:HAS_CHUNK]->(c:Chunk)
        RETURN i.key AS key, count(c) AS chunk_count
        LIMIT 5
        """)
        if res:
            for record in res:
                print(f"  * Issue {record['key']} has {record['chunk_count']} linked text chunks")
        else:
            print("  No chunk-to-issue links found.")

    finally:
        graph_store.close()
        print("=" * 60)


if __name__ == "__main__":
    test_graph_db()
