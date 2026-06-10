# Confluence Ingestion

This guide covers the Confluence-specific ingestion path for the backend.

## 1. Set environment variables

Update [backend/.env](backend/.env) with your Confluence credentials:

```env
CONFLUENCE_URL=https://pravatjana.atlassian.net/
CONFLUENCE_USERNAME=your-atlassian-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
CONFLUENCE_SPACE=
CONFLUENCE_PAGE_IDS=
ENABLE_CONFLUENCE_INGEST=true
```

### Notes
- Use either `CONFLUENCE_SPACE` or `CONFLUENCE_PAGE_IDS`.
- `CONFLUENCE_PAGE_IDS` should be a comma-separated list of page IDs.
- If you set `ENABLE_CONFLUENCE_INGEST=false`, only PDF ingestion will run.

## 2. Run ingestion

From the backend folder:

```powershell
cd backend
python ingest.py
```

The ingestion flow will:
1. load PDF files from `pdf_documents/` (existing behavior)
2. also fetch Confluence pages and run the same chunk → embed → store pipeline

## 3. Troubleshooting

- If Confluence pages are not being ingested, check that your API token has access to the target space.
- If you want to ingest only specific pages, set `CONFLUENCE_PAGE_IDS`.
