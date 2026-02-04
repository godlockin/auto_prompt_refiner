# API Reference

This document describes the API endpoints for Synthesis Prime.

## Base URL

- **Local Development**: `http://localhost:8787/api`
- **Production**: `/api` (Cloudflare Pages)

## Authentication

All API endpoints require an invite code via the `x-invite-code` header:

```
x-invite-code: your-invite-code
```

---

## Endpoints

### Health Check

**GET** `/api/health`

Returns system health status.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-04T12:00:00Z",
  "components": {
    "api": { "status": "healthy" },
    "kv": { "status": "healthy" },
    "config": { "status": "healthy", "missing_vars": [] }
  }
}
```

---

### Refine Prompt

**POST** `/api/refine`

Refines a user prompt using the Synthesis Prime cognitive architecture.

**Request Body**:
```json
{
  "prompt": "Help me write a Python function to calculate fibonacci numbers efficiently."
}
```

**Response**: Server-Sent Events (SSE)

```json
{"type": "log", "content": "🔍 Phase 1: Analyzing Intent & Strategy..."}
{"type": "chunk", "content": "## Role: Python Expert..."}
{"type": "final", "content": "## Role: Python Performance Expert..."}
```

**Rate Limits**:
- `/api/refine`: 20 requests per minute
- `/api/history`: 100 requests per minute

---

### History

**GET** `/api/history`

Returns list of past refinement tasks.

**Response (200 OK)**:
```json
[
  {
    "id": "1700000000000",
    "original": "Help me write fibonacci",
    "final": "## Role: Python Expert...",
    "timestamp": "2026-02-04T12:00:00Z"
  }
]
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid invite code |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |
