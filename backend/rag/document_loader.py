import os

from bs4 import BeautifulSoup
from atlassian import Confluence
from pypdf import PdfReader


def load_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text()

    return text


DEFAULT_CONFLUENCE_URL = "https://pravatjana.atlassian.net/"


def load_confluence_pages(space=None, page_ids=None):
    """Load Confluence pages into plain text for the existing chunking pipeline."""
    url = os.getenv("CONFLUENCE_URL", DEFAULT_CONFLUENCE_URL)
    username = os.getenv("CONFLUENCE_USERNAME")
    token = os.getenv("CONFLUENCE_API_TOKEN")

    if not all([url, username, token]):
        return []

    confluence = Confluence(
        url=url,
        username=username,
        password=token,
        api_version="cloud",
    )

    selected_space = space or os.getenv("CONFLUENCE_SPACE")
    selected_page_ids = page_ids or os.getenv("CONFLUENCE_PAGE_IDS", "").split(",")

    if selected_page_ids and selected_page_ids != [""]:
        page_ids_to_fetch = [page_id.strip() for page_id in selected_page_ids if page_id.strip()]
    else:
        pages = confluence.get_all_pages_from_space(selected_space, start=0, limit=50)
        page_ids_to_fetch = [str(page["id"]) for page in pages]

    documents = []

    for page_id in page_ids_to_fetch:
        page = confluence.get_page_by_id(page_id, expand="body.storage")
        title = page.get("title", f"confluence_{page_id}")
        html = page.get("body", {}).get("storage", {}).get("value", "")
        text = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
        documents.append((f"{title}.html", text))

    return documents


# print(load_pdf("E:\AgentMesh\rag\data\AI_in_Medicine.pdf"))