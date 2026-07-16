# Backend Run Guide

This guide explains how to run the backend locally.

## 1. Open the backend folder

```powershell
cd D:\AgentMesh\backend
```

## 2. Create or activate the virtual environment

If the virtual environment is not created yet:

```powershell
uv venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
uv sync
```

## 4. Configure environment variables

Make sure `.env` contains the values needed by the backend.

Important variables:

- `ANTHROPIC_API_KEY`
- `ATLASSIAN_EMAIL`
- `ATLASSIAN_API_TOKEN`
- `ATLASSIAN_BASE_URL`
- `CONFLUENCE_URL`
- `CONFLUENCE_USERNAME`
- `CONFLUENCE_API_TOKEN`
- `CONFLUENCE_SPACE`
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`

Notes:

- Jira and Confluence ingestion need the Atlassian values.
- Answer generation and hybrid query parsing use the Anthropic API key.
- Graph enrichment uses Neo4j. If Neo4j is unavailable, the main retrieval flow still works, but parent/child graph context may fail.

## 5. Add source data

### PDF

Place PDF files inside:

```text
D:\AgentMesh\backend\pdf_documents
```

### Jira / Confluence

The backend currently loads Jira and Confluence content from the configured Atlassian environment.

## 6. Ingest the data

This step:

- chunks PDFs, Jira issues, and Confluence pages
- creates embeddings
- stores chunks, embeddings, and metadata in ChromaDB

Run:

```powershell
uv run python ingest.py
```

If you want a fresh ingest, delete or rename:

```text
D:\AgentMesh\backend\chroma_db
```

and then run ingestion again.

## 7. Start the API server

```powershell
uv run uvicorn api.app:app --reload
```

The backend will start on:

```text
http://127.0.0.1:8000
```

## 8. Test the chat endpoint

Example request:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"query":"show me done work about password reset"}'
```

## 9. What the backend does at query time

Current flow:

1. Receives the raw user query.
2. Parses the query into:
   - cleaned semantic query
   - hard filters
   - soft source scopes
3. Runs scoped retrieval over Jira, Confluence, and/or PDF subsets.
4. Runs both:
   - vector retrieval
   - BM25 retrieval
5. Merges and reranks the candidate chunks.
6. Generates the final answer.

## 10. Useful files

Main API:

- [api/app.py](D:/AgentMesh/backend/api/app.py:1)

Query understanding:

- [rag/query_parser.py](D:/AgentMesh/backend/rag/query_parser.py:1)

Hybrid retrieval:

- [rag/hybrid_retriver.py](D:/AgentMesh/backend/rag/hybrid_retriver.py:1)
- [rag/retreiver.py](D:/AgentMesh/backend/rag/retreiver.py:1)
- [rag/bm25_retriever.py](D:/AgentMesh/backend/rag/bm25_retriever.py:1)

Ingestion:

- [ingest.py](D:/AgentMesh/backend/ingest.py:1)
- [chunking/pdf_ingestion.py](D:/AgentMesh/backend/chunking/pdf_ingestion.py:1)
- [chunking/structured_text_ingestion.py](D:/AgentMesh/backend/chunking/structured_text_ingestion.py:1)

## 11. Common issues

### No results returned

Possible reasons:

- ingestion has not been run
- `chroma_db` is empty
- filters are too strict

### Jira / Confluence data not loading

Check:

- Atlassian credentials in `.env`
- correct `CONFLUENCE_SPACE`
- network access to Atlassian

### Anthropic parsing or answer generation fails

Check:

- `ANTHROPIC_API_KEY`

If the LLM-based parser fails, the backend falls back to rule-based parsing.

### Graph errors from Neo4j

If Neo4j is unavailable, you may see graph lookup errors. The main answer flow still works, but graph enrichment may be missing.
