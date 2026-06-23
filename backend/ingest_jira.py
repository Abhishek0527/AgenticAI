from connectors.jira_loader import load_jira, issue_to_text
from rag.vectorstore import store_embeddings
from rag.embedding import embed_chunks
from rag.chunker import chunk_text
from rag.graphstore import GraphStore


def ingest_jira():

    graph_store = GraphStore()

    try:
        issues = load_jira()

        print(f"Total Jira Issues: {len(issues)}")

        for issue in issues:

            ticket_id = issue["key"]

            print(f"\nProcessing: {ticket_id}")

            text = issue_to_text(issue)

            chunks = chunk_text(text)

            metadatas = []

            for index, _ in enumerate(chunks):

                metadatas.append(
                    {
                        "source_type": "jira",
                        "ticket_id": ticket_id,
                        "chunk_index": index
                    }
                )

            embeddings = embed_chunks(chunks)

            # Store embeddings in ChromaDB and get the unique chunk IDs
            ids = store_embeddings(
                chunks,
                embeddings,
                metadatas
            )

            # Ingest issue metadata & relationships to Neo4j Graph DB
            graph_store.ingest_jira_issue(issue)

            # Link the chunk nodes to the issue node in Neo4j Graph DB
            graph_store.link_chunks_to_issue(ticket_id, chunks, ids)

            print(f"Finished: {ticket_id}")
            print(f"Chunks Stored: {len(chunks)}")

    finally:
        graph_store.close()


if __name__ == "__main__":
    ingest_jira()