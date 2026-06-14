import os
from dotenv import load_dotenv
from atlassian import Confluence
from bs4 import BeautifulSoup

load_dotenv()

DEFAULT_CONFLUENCE_URL = "https://agenticevo.atlassian.net/"

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
    print("SPACE:", selected_space)
    selected_page_ids = page_ids or os.getenv("CONFLUENCE_PAGE_IDS", "").split(",")

    if selected_page_ids and selected_page_ids != [""]:
        page_ids_to_fetch = [page_id.strip() for page_id in selected_page_ids if page_id.strip()]
    else:
        pages = confluence.get_all_pages_from_space(selected_space, start=0, limit=50)
        page_ids_to_fetch = [str(page["id"]) for page in pages]
        print("Pages found:", len(pages))

        for page in pages:
            print(page["id"], page["title"])

    documents = []

    for page_id in page_ids_to_fetch:
        page = confluence.get_page_by_id(page_id, expand="body.storage")
        title = page.get("title", f"confluence_{page_id}")
        html = page.get("body", {}).get("storage", {}).get("value", "")
        text = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
        documents.append((f"{title}.html", text))

    return documents

if __name__ == "__main__":
    load_confluence_pages()

