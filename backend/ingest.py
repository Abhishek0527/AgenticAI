from connectors.confluence_loader import load_confluence_pages
from rag.vectorstore import store_embeddings
from rag.embedding import embed_chunks
from chunking.pdf_ingestion import (
    build_pdf_chunks_with_metadata
)
from chunking.structured_text_ingestion import (
    build_confluence_chunks_with_metadata,
    build_jira_chunks_with_metadata,
)

from connectors.jira_loader import (
    load_jira
)

import os


def ingest_pdfs():

    pdf_folder = "./pdf_documents"

    pdf_files = [
        file
        for file in os.listdir(pdf_folder)
        if file.endswith(".pdf")
    ]

    for pdf_file in pdf_files:

        pdf_path = os.path.join(
            pdf_folder,
            pdf_file
        )

        print(f"\nProcessing PDF: {pdf_file}")

        chunks, metadatas = build_pdf_chunks_with_metadata(
            pdf_path
        )

        embeddings = embed_chunks(chunks)

        store_embeddings(
            chunks,
            embeddings,
            metadatas
        )

        print(f"Finished PDF: {pdf_file}")
        print(f"Chunks Stored: {len(chunks)}")


def ingest_confluence():

    pages = load_confluence_pages()

    print(
        f"\nTotal Confluence Pages: {len(pages)}"
    )

    for page in pages:

        source_name = page["title"]
        parent_title = page["parent_title"]
        print(
            f"\nProcessing Confluence: {source_name}"
        )

        chunks, metadatas = (
            build_confluence_chunks_with_metadata(
                page
            )
        )

        embeddings = embed_chunks(chunks)

        store_embeddings(
            chunks,
            embeddings,
            metadatas
        )

        print(
            f"Finished Confluence: {source_name}"
        )

        print(
            f"Chunks Stored: {len(chunks)}"
        )


def ingest_jira():

    issues = load_jira()

    print(
        f"\nTotal Jira Issues: {len(issues)}"
    )

    for issue in issues:

        ticket_id = issue["key"]

        title = issue["fields"]["summary"]

        issue_type = (
            issue["fields"]["issuetype"]["name"]
        )

        parent = issue["fields"].get("parent")

        parent_key = ""

        if parent:
            parent_key = parent["key"]

        print(
            f"\nProcessing Jira: {ticket_id}"
        )

        chunks, metadatas = (
            build_jira_chunks_with_metadata(
                issue
            )
        )

        embeddings = embed_chunks(chunks)

        store_embeddings(
            chunks,
            embeddings,
            metadatas
        )

        print(
            f"Finished Jira: {ticket_id}"
        )

        print(
            f"Chunks Stored: {len(chunks)}"
        )


def ingest():

    ingest_pdfs()

    ingest_jira()

    ingest_confluence()


if __name__ == "__main__":

    ingest()
