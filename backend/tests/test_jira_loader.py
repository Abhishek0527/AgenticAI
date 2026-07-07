import unittest
from unittest.mock import patch

from connectors.jira_loader import load_jira


class JiraLoaderTests(unittest.TestCase):
    @patch.dict("os.environ", {"ATLASSIAN_EMAIL": "user@example.com", "ATLASSIAN_API_TOKEN": "token", "ATLASSIAN_BASE_URL": "https://example.atlassian.net", "JIRA_PROJECT_KEY": "GENAI"}, clear=False)
    @patch("connectors.jira_loader.requests.get")
    def test_load_jira_uses_configured_project_key(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"issues": []}

        load_jira()

        self.assertEqual(mock_get.call_count, 1)
        called_params = mock_get.call_args.kwargs["params"]
        self.assertEqual(called_params["jql"], "project=GENAI")


if __name__ == "__main__":
    unittest.main()
