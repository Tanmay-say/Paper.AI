# PaperAI API Documentation

Base URL: `https://researchgenius.preview.emergentagent.com/api`

## Authentication
No authentication required for this version.

---

## Endpoints

### 1. Health Check
Check the health status of the API and Neo4j connection.

**Endpoint:** `GET /health`

**Example:**
```bash
curl -X GET "https://researchgenius.preview.emergentagent.com/api/health"
```

**Response:**
```json
{
  "status": "healthy",
  "neo4j": "connected"
}
```

---

### 2. Search Papers
Search for research papers from arXiv.

**Endpoint:** `POST /papers/search`

**Request Body:**
```json
{
  "query": "transformer attention mechanism",
  "max_results": 10,
  "source": "arxiv"
}
```

**Example:**
```bash
curl -X POST "https://researchgenius.preview.emergentagent.com/api/papers/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural networks deep learning",
    "max_results": 5
  }'
```

**Response:**
```json
[
  {
    "paper_id": "2103.14030",
    "title": "Swin Transformer: Hierarchical Vision Transformer using Shifted Windows",
    "authors": ["Ze Liu", "Yutong Lin", "..."],
    "abstract": "This paper presents a new vision Transformer...",
    "year": 2021,
    "source": "arxiv",
    "pdf_url": "https://arxiv.org/pdf/2103.14030.pdf",
    "arxiv_id": "2103.14030",
    "published_date": "2021-03-25T17:58:27+00:00"
  }
]
```

---

### 3. Get Paper Details
Get detailed information about a specific paper from Neo4j.

**Endpoint:** `GET /papers/{paper_id}`

**Example:**
```bash
curl -X GET "https://researchgenius.preview.emergentagent.com/api/papers/2103.14030v2"
```

**Response:**
```json
{
  "paper_id": "2103.14030v2",
  "title": "Swin Transformer: Hierarchical Vision Transformer using Shifted Windows",
  "authors": ["Ze Liu", "Yutong Lin"],
  "abstract": "This paper presents...",
  "year": 2021,
  "source": "arxiv",
  "pdf_path": "./storage/pdfs/2103.14030.pdf",
  "citation_count": 0,
  "related_papers": []
}
```

---

### 4. Get Paper PDF
Stream or download the PDF file for a paper.

**Endpoint:** `GET /papers/{paper_id}/pdf`

**Example:**
```bash
curl -X GET "https://researchgenius.preview.emergentagent.com/api/papers/2103.14030v2/pdf" \
  --output paper.pdf
```

**Note:** The paper must be ingested first before the PDF is available.

---

### 5. Chat Query (Non-Streaming)
Ask questions about a paper and get AI-generated answers.

**Endpoint:** `POST /chat/query`

**Request Body:**
```json
{
  "paper_id": "2103.14030",
  "query": "What is the main contribution of this paper?",
  "selected_text": "Optional: text selected from PDF",
  "chat_history": []
}
```

**Example:**
```bash
curl -X POST "https://researchgenius.preview.emergentagent.com/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_id": "2103.14030",
    "query": "What is the Swin Transformer architecture?",
    "selected_text": null,
    "chat_history": []
  }'
```

**Response:**
```json
{
  "response": "The Swin Transformer is a hierarchical vision Transformer that uses shifted windows...",
  "sources": [
    {
      "chunk_id": "2103.14030_chunk_5",
      "paper_id": "2103.14030",
      "text": "The Swin Transformer architecture consists of...",
      "score": 0.89
    }
  ],
  "paper_id": "2103.14030"
}
```

---

### 6. Ingest Papers
Trigger background ingestion of papers into the system.

**Endpoint:** `POST /ingest/papers`

**Request Body:**
```json
{
  "paper_ids": ["2103.14030", "1706.03762"],
  "source": "arxiv"
}
```

**Example:**
```bash
curl -X POST "https://researchgenius.preview.emergentagent.com/api/ingest/papers" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_ids": ["2103.14030"],
    "source": "arxiv"
  }'
```

**Response:**
```json
{
  "job_id": "7325667b-8cd7-44e2-9602-c5ec0e88c29c",
  "status": "pending",
  "total_papers": 1,
  "processed_papers": 0,
  "failed_papers": 0,
  "message": "Ingestion job started"
}
```

**Note:** Ingestion is processed asynchronously by Celery workers. A typical paper takes 15-30 seconds to ingest.

---

### 7. Get Ingestion Status
Check the status of a paper ingestion job.

**Endpoint:** `GET /ingest/status/{job_id}`

**Example:**
```bash
curl -X GET "https://researchgenius.preview.emergentagent.com/api/ingest/status/7325667b-8cd7-44e2-9602-c5ec0e88c29c"
```

**Response:**
```json
{
  "job_id": "7325667b-8cd7-44e2-9602-c5ec0e88c29c",
  "status": "processing",
  "total_papers": 1,
  "processed_papers": 0,
  "failed_papers": 0,
  "message": "Status tracking to be implemented with Redis"
}
```

---

## WebSocket Endpoint

### Chat with Streaming
Real-time chat with streaming responses.

**Endpoint:** `WS /ws/chat`

**Connection URL:**
```
wss://researchgenius.preview.emergentagent.com/api/ws/chat
```

**Send Message:**
```json
{
  "paper_id": "2103.14030",
  "query": "Explain the shifted window approach",
  "selected_text": null,
  "chat_history": []
}
```

**Receive Messages:**
The server will send multiple JSON messages:

1. Sources:
```json
{
  "type": "sources",
  "data": [...]
}
```

2. Content chunks (streaming):
```json
{
  "type": "content",
  "data": "The shifted window..."
}
```

3. Completion:
```json
{
  "type": "done",
  "data": null
}
```

---

## Complete Testing Workflow

### 1. Search for a Paper
```bash
curl -X POST "https://researchgenius.preview.emergentagent.com/api/papers/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "attention is all you need", "max_results": 1}'
```

### 2. Ingest the Paper
```bash
curl -X POST "https://researchgenius.preview.emergentagent.com/api/ingest/papers" \
  -H "Content-Type: application/json" \
  -d '{"paper_ids": ["<paper_id_from_search>"], "source": "arxiv"}'
```

### 3. Wait 20-30 seconds for ingestion to complete

### 4. Query the Paper
```bash
curl -X POST "https://researchgenius.preview.emergentagent.com/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_id": "<paper_id>",
    "query": "What is the main idea?",
    "chat_history": []
  }'
```

---

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Notes

1. **Paper IDs**: arXiv paper IDs may include version suffixes (e.g., "2103.14030v2")
2. **Ingestion Required**: Papers must be ingested before PDF viewing and chat features work
3. **Rate Limiting**: No rate limiting currently implemented
4. **Storage**: PDFs are stored locally in `/app/storage/pdfs/`
5. **Graph Database**: All paper metadata and chunks are stored in Neo4j with vector embeddings
