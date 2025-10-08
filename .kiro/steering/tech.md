# Technical Architecture

## Core Stack

- **Python**: 3.11+
- **API Framework**: FastAPI for BFF layer
- **Orchestration**: LangGraph for multi-agent pipeline coordination
- **Database**: SQLAlchemy + Alembic for ORM and migrations
- **Infrastructure**: Neon Postgres, Pinecone vector storage, OpenAI APIs

## LangGraph Orchestration Framework

### StateGraph Architecture
- Define coding and theme development stages with typed state
- Node functions wrap agent logic (coder, aggregator, reviewer, theme-coder, theme-aggregator)
- Conditional edges route between pipeline stages based on state
- Supports both sequential and parallel execution patterns

### PostgresSaver for Checkpointing
- Persistent state recovery across pipeline stages
- Checkpoint after coding stage (consolidated codebook) and theme stage (final themes)
- Enables resume from failure without reprocessing expensive LLM calls
- Serialized as JSON blobs in `analysis_checkpoints` table

### Send API for Dynamic Parallelization
- Dynamically spawn multiple coder agents across identities or data partitions
- Scale out work based on identity diversity (multiple perspectives) or work partitioning (throughput)
- Concurrent execution bounded by API rate limits and cost controls

## Infrastructure

### Neon Postgres
- **Database**: `eq-dev-thematic`
- **Multi-tenancy**: Row-Level Security (RLS) enforced via `app.current_account_id` session variable
- **Roles**:
  - `app_user`: RLS enabled for all user-facing queries
  - `db_service`: BYPASSRLS for internal pipeline operations (checkpointing, migrations)
  - `migrations`: Schema modification only, no data access
- **Connection**: Endpoint configured in `.env` (never committed)

### Pinecone
- Vector storage for code embeddings
- Enables semantic similarity search for code merging in reviewer agent
- Embeddings generated using OpenAI `text-embedding-3-large`

### OpenAI
- **Primary Model**: GPT-4o for coder, aggregator, reviewer, and theme agents
- **Embeddings**: `text-embedding-3-large` for code similarity
- API keys stored in `.env` with secure handling

## Development Tools

- **Dependency Management**: `uv` or `poetry`
- **Testing**: `pytest` with unit, contract, integration, and E2E levels
- **Linting**: `ruff` with default rules
- **Type Checking**: `mypy` in strict mode
- **Pre-commit Hooks**: Enforce formatting, linting, and type checks before commit

## Feature Flags

Environment variables for controlling behavior:

- `LIVE_TESTS` (default: 0): Gate integration/E2E tests that call real APIs
- `DRY_RUN` (default: 1): Simulate LLM calls without actual API requests
- `COST_BUDGET_USD` (default: 5.00): Maximum allowed cost per analysis request

## Cost Guardrails (v1 Simplified)

### Budget Fail-Fast
- Estimate token usage before execution based on interaction count and average tokens
- Reject analysis requests exceeding `COST_BUDGET_USD` with 400 Bad Request
- Return estimated cost in 202 response for accepted jobs

### Rate Limiting
- Respect provider TPS/RPM limits with configurable throttling
- Maintain short-term request counters to stay within safe bounds
- Queue or delay requests approaching limits

### Retry Strategy
- Exponential backoff for transient failures (timeouts, 5xx errors)
- Maximum 3 retries per LLM call
- No global circuit breaker in v1; rely on retries and backoff only

## Checkpoint Management

### Retention Policy
- **Completed jobs**: Retain checkpoints for 7 days post-completion for debugging
- **Failed jobs**: Retain checkpoints for 30 days for incident investigation
- **Cleanup**: Daily job purges expired checkpoints

### Storage Strategy
- PostgresSaver with JSON serialization
- Checkpoints keyed by `analysis_id` and stage marker
- Include timestamps, status, and serialized state (codebook, themes)

## Observability (v1 Scope)

### Health Endpoints
- `/health`: Basic service health check
- `/health/db`: Database connectivity check
- `/health/llm`: LLM API connectivity check (optional, may incur cost)

### Structured Logging
- JSON format with required fields: `timestamp`, `level`, `logger`, `message`, `tenant_id`, `analysis_id`, `trace_id`
- Scrub PII from logs; never log raw interaction text at INFO level
- Use DEBUG level with explicit opt-in for content logging

### Deferred to Post-v1
- Metrics dashboards (Prometheus/Grafana)
- Advanced tracing (distributed tracing with OpenTelemetry)
- Alerting on anomalies (cost spikes, error rates)

## Theme Compression Strategy

### Primary: LLMLingua
- Use LLMLingua (via LangChain `DocumentCompressor`) when codebook exceeds thresholds:
  - More than 100 codes, OR
  - More than 50k tokens
- Compress code descriptions while preserving:
  - All code IDs
  - At least 1 representative quote per code
- Compression is input-only for theme-coder agents; full codebook always preserved in storage

### Fallback: Simple Truncation/Summarization
- If LLMLingua unavailable or fails, use basic summarizer with identical preservation rules
- Truncate descriptions to fit context window while maintaining code IDs and quotes
- Log fallback usage for monitoring

## MCP Configuration

### Workspace-Scoped Config
- Location: `.kiro/settings/mcp.json` (workspace level) or `~/.kiro/settings/mcp.json` (user level)
- Workspace config takes precedence in case of conflicts on server name

### Available MCP Servers

#### GitHub MCP (Primary Development Aid)
- Access LangGraph repository for code examples and patterns
- Reference StateGraph examples, Send API usage, checkpointer implementations
- No auto-approve for write/destructive operations

#### Neon MCP (Primary Development Aid)
- Direct database queries and schema inspection
- Database: `eq-dev-thematic`
- Use for schema validation during development
- Endpoint configured in `.env`

#### LangGraph Docs MCP (Primary Development Aid)
- Official LangGraph documentation access
- API references and best practices
- Compression strategies and DocumentCompressor usage

#### Brave Search MCP (Supplementary Research)
- External documentation and context lookup
- Use for supplementary research only

#### Context7 MCP (Supplementary Research)
- Additional context and reference retrieval
- Use for supplementary research only

### Usage Policy
- Primary: GitHub, Neon, and LangGraph Docs MCPs for development
- Supplementary: Brave/Context7 for research
- No auto-approve for write/destructive operations
- Verify configuration before first use; generate stub if missing

### Integration Notes
- Use GitHub MCP to reference LangGraph patterns (StateGraph, Send API, checkpointers)
- Use Neon MCP for schema validation during development
- Use LangGraph Docs MCP for compression strategies and DocumentCompressor usage
- List MCP tool names in `autoApprove` section for frequently used read-only operations
- Set `disabled: true` to disable a server without removing configuration
