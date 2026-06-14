import os
import requests
from dotenv import load_dotenv

load_dotenv()


def extract_text(node):

    texts = []

    if isinstance(node, dict):

        if "text" in node:
            texts.append(node["text"])

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

    url = f"{base_url}/rest/api/3/search/jql"

    params = {
        "jql": "project=SCRUM",
        "fields": "summary,description,status"
    }

    response = requests.get(
        url,
        auth=(email, token),
        params=params
    )

    response.raise_for_status()

    data = response.json()

    return data["issues"]


if __name__ == "__main__":

    issues = load_jira()

    print(f"Total Issues: {len(issues)}")
    print()

    for issue in issues:

        text = issue_to_text(issue)

        print(text)
        print("=" * 100)