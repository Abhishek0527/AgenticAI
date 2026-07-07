import unittest

from jira_graph_ingest import create_jira_graph


class FakeSession:
    def __init__(self):
        self.queries = []

    def run(self, query, **params):
        self.queries.append((query, params))


class JiraGraphIngestTests(unittest.TestCase):
    def test_create_jira_graph_creates_nodes_and_relationships(self):
        session = FakeSession()
        issues = [
            {
                "key": "GENAI-2",
                "fields": {
                    "summary": "Task 3",
                    "issuetype": {"name": "Story"},
                    "parent": {"key": "GENAI-1"},
                },
            },
            {
                "key": "GENAI-1",
                "fields": {
                    "summary": "Epic 1",
                    "issuetype": {"name": "Epic"},
                    "parent": None,
                },
            },
        ]

        create_jira_graph(session, issues)

        self.assertTrue(any("MERGE (n:Jira" in query for query, _ in session.queries))
        self.assertTrue(any("MERGE (parent)-[:HAS_TICKET]->(child)" in query for query, _ in session.queries))


if __name__ == "__main__":
    unittest.main()
