import os
import requests
from dotenv import load_dotenv

load_dotenv()


def extract_text(node):

    texts = []

    if isinstance(node, dict):

        if "text" in node:
            texts.append(node["text"])

        # Capture URLs from inlineCard/blockCard nodes (Confluence smart-links)
        if node.get("type") in ("inlineCard", "blockCard"):
            url = node.get("attrs", {}).get("url", "")
            if url:
                texts.append(url)

        for value in node.values():
            texts.extend(extract_text(value))

    elif isinstance(node, list):

        for item in node:
            texts.extend(extract_text(item))

    return texts


def issue_to_text(issue):

    key = issue["key"]

    summary = issue["fields"]["summary"]

    status = issue["fields"]["status"]["name"]

    description = issue["fields"]["description"]

    description_text = "\n".join(
        extract_text(description)
    )

    return f"""
Ticket ID: {key}

Title: {summary}

Description:
{description_text}

Status:
{status}
"""

def load_jira():

    email = os.getenv("ATLASSIAN_EMAIL")
    token = os.getenv("ATLASSIAN_API_TOKEN")
    base_url = os.getenv("ATLASSIAN_BASE_URL")
    project_key = (
        os.getenv("JIRA_PROJECT_KEY")
        or os.getenv("JIRA_SPACE")
        or os.getenv("JIRA_PROJECT")
        or "SCRUM"
    )

    url = f"{base_url}/rest/api/3/search/jql"

    params = {
        "jql": f"project={project_key}",
        "fields": (
            "summary,"
            "description,"
            "status,"
            "parent,"
            "issuetype"
        )
    }

    response = requests.get(
        url,
        auth=(email, token),
        params=params
    )

    response.raise_for_status()

    return response.json()["issues"]


if __name__ == "__main__":

    issues = load_jira()

    for issue in issues:

        fields = issue["fields"]

        parent = fields.get("parent")

        print("\n-----------------------")

        print("Key:", issue["key"])

        print(
            "Type:",
            fields["issuetype"]["name"]
        )

        print(
            "Title:",
            fields["summary"]
        )

        print(
            "Parent:",
            parent["key"]
            if parent else None
        )
