# RAG Module

## Overview

This module implements a Retrieval-Augmented Generation (RAG) pipeline.

Current Flow:

PDF → Text → Chunks → Embeddings → ChromaDB → Retrieval → Claude → Answer

---

## Architecture

### document_loader.py

Responsibility:

* Load PDF files
* Extract text from all pages
* Return a single text string

Input:

```python
pdf_path
```

Output:

```python
text
```

---

### chunker.py

Responsibility:

* Split large text into smaller chunks
* Preserve context using overlap

Input:

```python
text
```

Output:

```python
list[str]
```

Example:

```python
[
    "React is a JavaScript library...",
    "Components are reusable..."
]
```

---

### embedding.py

Responsibility:

* Convert text chunks into vector embeddings
* Convert user queries into embeddings

Model:

```text
all-MiniLM-L6-v2
```

Input:

```python
list[str]
```

Output:

```python
list[list[float]]
```

Example:

```python
[
    [0.12, -0.44, ...],
    [0.91, 0.22, ...]
]
```

---

### vector_store.py

Responsibility:

* Store chunks and embeddings inside ChromaDB

Stored Data:

```python
{
    "id": "chunk_0",
    "document": "...",
    "embedding": [...]
}
```

Input:

```python
chunks
embeddings
```

Output:

```text
Stored in ChromaDB
```

---

### retriever.py

Responsibility:

* Convert user query into embedding
* Search ChromaDB
* Return top matching chunks

Flow:

```text
User Query
↓
Query Embedding
↓
Vector Search
↓
Top 3 Chunks
```

Input:

```python
query
```

Output:

```python
[
    chunk1,
    chunk2,
    chunk3
]
```

---

### generator.py

Responsibility:

* Create prompt using retrieved chunks
* Send prompt to Claude
* Generate final answer

Flow:

```text
Retrieved Chunks
+
User Query
↓
Claude
↓
Final Answer
```

---

## End-to-End Flow

```text
User Query
↓
Generate Query Embedding
↓
Search ChromaDB
↓
Retrieve Top Chunks
↓
Create Prompt
↓
Claude
↓
Final Response
```

---

## Current Status

Completed:

* PDF Loading
* Chunking
* Embeddings
* ChromaDB Storage
* Retrieval
* Claude Integration
* End-to-End RAG Pipeline

Pending:

* Hallucination Detection
* Similarity Threshold
* Multi-PDF Support
* Reranking
* Conversation Memory
* LangGraph Integration

```
```
