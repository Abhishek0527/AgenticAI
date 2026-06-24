from connectors.confluence_loader import load_confluence_pages
from rag.vectorstore import store_embeddings
from rag.embedding import embed_chunks
from rag.chunker import chunk_text
from rag.document_loader import load_pdf

from connectors.jira_loader import (
    load_jira,
    issue_to_text
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

        text = load_pdf(pdf_path)

        chunks = chunk_text(text)

        metadatas = []

        for index, _ in enumerate(chunks):

            metadatas.append(
                {
                    "source_type": "pdf",
                    "source": pdf_file,
                    "title": pdf_file,
                    "project": "learning",
                    "chunk_index": index
                }
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
        text = page["text"]

        print(
            f"\nProcessing Confluence: {source_name}"
        )

        text = f"""
        Title: {source_name}

        Parent Page: {parent_title}

        {text}
        """

        chunks = chunk_text(text)

        metadatas = []

        for index, _ in enumerate(chunks):

            metadatas.append(
                {
                    "source_type": "confluence",
                    "source": source_name,
                    "title": source_name,
                    "parent_title": parent_title,
                    "project": "authentication_platform",
                    "chunk_index": index
                }
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

        text = issue_to_text(issue)

        text = f"""
        Ticket ID: {ticket_id}

        Title: {title}

        Issue Type: {issue_type}

        Parent Ticket: {parent_key}

        {text}
        """

        chunks = chunk_text(text)

        metadatas = []

        for index, _ in enumerate(chunks):

            metadatas.append(
                {
                    "source_type": "jira",
                    "source": ticket_id,
                    "title": title,
                    "issue_type": issue_type,
                    "parent_key": parent_key,
                    "project": "authentication_platform",
                    "chunk_index": index
                }
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