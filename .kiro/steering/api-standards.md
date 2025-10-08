# API Standards

## Format

- **Request/Response**: JSON for all requests and responses
- **Content-Type**: `application/json`
- **Character Encoding**: UTF-8

## Error Envelope

Standard error structure for all error responses:

```json
{
  "error": {
    "code": "COST_LIMIT_EXCEEDED",
    "message": "Estimated cost ($12.50) exceeds budget limit ($5.00)",
    "detail": "Reduce the date range or increase COST_BUDGET_USD"
  }
}
```

### Error Fields
- `code`: Machine-readable error code (UPPER_SNAKE_CASE)
- `message`: Human-readable error message
- `detail`: Optional additional context or suggested actions

### Common Error Codes
- `COST_LIMIT_EXCEEDED`: Analysis cost exceeds budget
- `INVALID_DATE_RANGE`: Invalid or out-of-bounds date range
- `UNAUTHORIZED`: Missing or invalid authentication
- `FORBIDDEN`: Insufficient permissions for requested resource
- `NOT_FOUND`: Requested resource does not exist
- `RATE_LIMIT_EXCEEDED`: Too many requests; retry after delay
- `INTERNAL_ERROR`: Unexpected server error

## Pagination

Cursor-based pagination for list endpoints:

```json
{
  "data": [...],
  "pagination": {
    "limit": 50,
    "cursor": "eyJpZCI6MTIzNDU2fQ==",
    "has_more": true
  }
}
```

### Pagination Fields
- `limit`: Number of items per page (default: 50, max: 100)
- `cursor`: Opaque cursor for next page (base64-encoded)
- `has_more`: Boolean indicating if more results exist

### Request Parameters
- `limit`: Optional; number of items to return (1-100)
- `cursor`: Optional; cursor from previous response for next page

## 202 + Polling Semantics

### Async Job Submission

**POST /analyze** triggers async analysis job:

```json
// Request
{
  "account_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "idempotency_key": "analysis-2024-01-550e8400"  // Optional
}

// Response: 202 Accepted
{
  "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "estimated_cost_usd": 2.50,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Status Polling

**GET /analysis/{analysis_id}** returns current status:

```json
// Pending
{
  "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}

// In Progress
{
  "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "in_progress",
  "progress": {
    "stage": "coding",
    "percent_complete": 45
  },
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:15Z"
}

// Completed
{
  "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "results": {
    "themes": [...],
    "codebook_version": "v42",
    "codes_generated": 87,
    "interactions_processed": 1250
  },
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:15Z",
  "completed_at": "2024-01-15T10:45:30Z"
}

// Failed
{
  "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "failed",
  "error": {
    "code": "LLM_SERVICE_UNAVAILABLE",
    "message": "OpenAI API unavailable after 3 retries",
    "detail": "Please retry later or contact support if issue persists"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:15Z",
  "failed_at": "2024-01-15T10:32:45Z"
}
```

### Status Values
- `pending`: Job queued, not yet started
- `in_progress`: Job actively processing
- `completed`: Job finished successfully; results available
- `failed`: Job failed; error details provided

## Idempotency

### POST /analyze Idempotency
- Accept optional `idempotency_key` in request body
- If key matches existing job (within 24 hours), return existing job details instead of creating duplicate
- Key format: client-defined string (max 255 chars); recommend: `{operation}-{date}-{account_id}`
- Idempotency window: 24 hours (keys expire after 24h)

### Implementation
- Store `idempotency_key` with `account_id` and `analysis_id` in database
- On POST, check for existing key before creating new job
- Return 202 with existing `analysis_id` if key found
- Clean up expired keys (>24h old) via daily job

## Rate Limiting

### 429 Too Many Requests

When rate limit exceeded:

```json
// Response: 429 Too Many Requests
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded: 10 requests per minute",
    "detail": "Retry after 45 seconds"
  }
}

// Headers
Retry-After: 45
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705318845
```

### Rate Limit Headers
- `Retry-After`: Seconds until rate limit resets
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

### Rate Limit Tiers (v1)
- **Default**: 10 requests per minute per account
- **Burst**: Allow up to 20 requests in 10-second burst, then enforce per-minute limit
- Future: Tiered limits based on account plan

## Authentication

### Bearer Token
- All requests require `Authorization: Bearer <token>` header
- Token encodes tenant/account context
- Invalid or missing token returns 401 Unauthorized

### Tenant Scoping
- All operations automatically scoped to authenticated tenant
- No cross-tenant access permitted
- Tenant ID extracted from token and set as `app.current_account_id` for RLS enforcement
