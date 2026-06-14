from connectors.jira_loader import load_jira, issue_to_text
from rag.vectorstore import store_embeddings
from rag.embedding import embed_chunks
from rag.chunker import chunk_text


def ingest_jira():

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

        store_embeddings(
            chunks,
            embeddings,
            metadatas
        )

        print(f"Finished: {ticket_id}")
        print(f"Chunks Stored: {len(chunks)}")


if __name__ == "__main__":
    ingest_jira()