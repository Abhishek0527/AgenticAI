import os
import re
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j.exceptions import DriverError, ServiceUnavailable

load_dotenv()


def extract_text_from_desc(node):
    """Recursively extract plain text from Jira description Rich Text/ADF node."""
    texts = []
    if isinstance(node, dict):
        if "text" in node:
            texts.append(node["text"])
        for value in node.values():
            texts.extend(extract_text_from_desc(value))
    elif isinstance(node, list):
        for item in node:
            texts.extend(extract_text_from_desc(item))
    return texts


def clean_relationship_type(text):
    """Normalize relationship types to uppercase with underscores, e.g., 'blocks' -> 'BLOCKS'."""
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    cleaned = cleaned.strip().upper().replace(" ", "_")
    return cleaned if cleaned else "LINKED_TO"


class GraphStore:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        self.driver = None
        self.enabled = False

        if not self.uri:
            print("GraphStore: NEO4J_URI environment variable not configured. Graph DB features disabled.")
            return

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Test connection
            self.driver.verify_connectivity()
            self.enabled = True
            print(f"GraphStore: Connected successfully to Neo4j at {self.uri}")
            self.create_constraints()
        except (ServiceUnavailable, DriverError) as e:
            print(f"GraphStore Warning: Could not connect to Neo4j at {self.uri}. Ingestion will proceed without Graph DB. Error: {e}")
            if self.driver:
                self.driver.close()
                self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()
            print("GraphStore: Neo4j connection closed.")

    def execute_query(self, query, parameters=None):
        if not self.enabled or not self.driver:
            return None
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters)
                return list(result)
        except Exception as e:
            print(f"GraphStore Query Error: Failed to execute query. Error: {e}")
            return None

    def create_constraints(self):
        if not self.enabled:
            return

        print("GraphStore: Creating schema constraints...")
        # Create constraints to ensure unique IDs for node types
        constraints = [
            "CREATE CONSTRAINT issue_key_unique IF NOT EXISTS FOR (i:Issue) REQUIRE i.key IS UNIQUE",
            "CREATE CONSTRAINT project_key_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.key IS UNIQUE",
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.accountId IS UNIQUE",
            "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE"
        ]
        
        for constraint in constraints:
            self.execute_query(constraint)

    def ingest_jira_issue(self, issue):
        if not self.enabled:
            return

        fields = issue.get("fields", {})
        key = issue.get("key")
        summary = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "")
        issuetype = fields.get("issuetype", {}).get("name", "Task")
        
        # Extract description
        desc_node = fields.get("description")
        description = "\n".join(extract_text_from_desc(desc_node)) if desc_node else ""

        print(f"GraphStore: Ingesting Issue {key} ({summary[:30]}...)")

        # 1. Upsert Issue Node
        issue_query = """
        MERGE (i:Issue {key: $key})
        SET i.summary = $summary,
            i.status = $status,
            i.type = $type,
            i.description = $description,
            i.source_type = "jira",
            i.updated_at = timestamp()
        """
        self.execute_query(issue_query, {
            "key": key,
            "summary": summary,
            "status": status,
            "type": issuetype,
            "description": description
        })

        # 2. Upsert Project and Link
        project = fields.get("project")
        if project and isinstance(project, dict):
            project_key = project.get("key")
            project_name = project.get("name", "")
            if project_key:
                project_query = """
                MERGE (p:Project {key: $project_key})
                ON CREATE SET p.name = $project_name
                WITH p
                MATCH (i:Issue {key: $key})
                MERGE (i)-[:BELONGS_TO]->(p)
                """
                self.execute_query(project_query, {
                    "key": key,
                    "project_key": project_key,
                    "project_name": project_name
                })

        # 3. Upsert Assignee and Link
        assignee = fields.get("assignee")
        if assignee and isinstance(assignee, dict):
            assignee_id = assignee.get("accountId")
            assignee_name = assignee.get("displayName", "")
            assignee_email = assignee.get("emailAddress", "")
            if assignee_id:
                assignee_query = """
                MERGE (u:User {accountId: $assignee_id})
                SET u.name = $assignee_name,
                    u.email = $assignee_email
                WITH u
                MATCH (i:Issue {key: $key})
                MERGE (i)-[:ASSIGNED_TO]->(u)
                """
                self.execute_query(assignee_query, {
                    "key": key,
                    "assignee_id": assignee_id,
                    "assignee_name": assignee_name,
                    "assignee_email": assignee_email
                })

        # 4. Upsert Reporter and Link
        reporter = fields.get("reporter")
        if reporter and isinstance(reporter, dict):
            reporter_id = reporter.get("accountId")
            reporter_name = reporter.get("displayName", "")
            reporter_email = reporter.get("emailAddress", "")
            if reporter_id:
                reporter_query = """
                MERGE (u:User {accountId: $reporter_id})
                SET u.name = $reporter_name,
                    u.email = $reporter_email
                WITH u
                MATCH (i:Issue {key: $key})
                MERGE (i)-[:REPORTED_BY]->(u)
                """
                self.execute_query(reporter_query, {
                    "key": key,
                    "reporter_id": reporter_id,
                    "reporter_name": reporter_name,
                    "reporter_email": reporter_email
                })

        # 5. Link Parent (Subtask/Epic Relationship)
        parent = fields.get("parent")
        if parent and isinstance(parent, dict):
            parent_key = parent.get("key")
            if parent_key:
                parent_query = """
                MERGE (parent:Issue {key: $parent_key})
                WITH parent
                MATCH (child:Issue {key: $key})
                MERGE (child)-[:SUBTASK_OF]->(parent)
                """
                self.execute_query(parent_query, {
                    "key": key,
                    "parent_key": parent_key
                })

        # 6. Issue Links (Blocks, Relates to, etc.)
        issuelinks = fields.get("issuelinks", [])
        for link in issuelinks:
            if not isinstance(link, dict):
                continue
            
            link_type = link.get("type", {})
            outward_desc = link_type.get("outward")
            
            # Check inward / outward issue
            if "outwardIssue" in link:
                target_key = link["outwardIssue"].get("key")
                rel_type = clean_relationship_type(outward_desc or "LINKS_TO")
                if target_key:
                    link_query = f"""
                    MATCH (source:Issue {{key: $source_key}})
                    MERGE (target:Issue {{key: $target_key}})
                    MERGE (source)-[:{rel_type}]->(target)
                    """
                    self.execute_query(link_query, {
                        "source_key": key,
                        "target_key": target_key
                    })
            elif "inwardIssue" in link:
                # inwardIssue means Target blocks Source, i.e. Target is outward blocker to Source
                target_key = link["inwardIssue"].get("key")
                rel_type = clean_relationship_type(outward_desc or "LINKS_TO")
                if target_key:
                    link_query = f"""
                    MERGE (target:Issue {{key: $target_key}})
                    WITH target
                    MATCH (source:Issue {{key: $source_key}})
                    MERGE (target)-[:{rel_type}]->(source)
                    """
                    self.execute_query(link_query, {
                        "source_key": key,
                        "target_key": target_key
                    })

    def link_chunks_to_issue(self, ticket_id, chunks, ids):
        if not self.enabled:
            return

        print(f"GraphStore: Linking {len(chunks)} chunks to Issue {ticket_id}")

        for index, (chunk_text, chunk_id) in enumerate(zip(chunks, ids)):
            chunk_query = """
            MATCH (i:Issue {key: $ticket_id})
            MERGE (c:Chunk {id: $chunk_id})
            SET c.text = $text,
                c.chunk_index = $chunk_index
            MERGE (i)-[:HAS_CHUNK]->(c)
            """
            self.execute_query(chunk_query, {
                "ticket_id": ticket_id,
                "chunk_id": chunk_id,
                "text": chunk_text,
                "chunk_index": index
            })
