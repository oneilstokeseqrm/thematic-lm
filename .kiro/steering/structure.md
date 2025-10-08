# Project Structure

## Source Layout

```
src/thematic_lm/
├── agents/          # Agent implementations (coder, aggregator, reviewer, theme agents)
├── orchestrator/    # LangGraph pipeline definitions and state management
├── models/          # SQLAlchemy models and Pydantic schemas
├── api/             # FastAPI BFF layer (routes, dependencies, middleware)
├── utils/           # Shared utilities (logging, cost estimation, compression)
└── config/          # Configuration classes and environment variable handling
```

## Tests Layout

```
tests/
├── unit/            # Pure logic tests with mocks; fast; no external dependencies
├── contract/        # Provider tests (BFF endpoints) and example validation
├── integration/     # Real DB (Neon with RLS), Pinecone, OpenAI API calls; gated by LIVE_TESTS=1
└── e2e/             # Full pipeline with small dataset (5-10 interactions); validates entire flow
```

## Configuration

### Environment Variables
- Stored in `.env` file (never committed; see `.env.example` for template)
- Loaded via `config.py` classes using Pydantic settings
- Required variables:
  - `DATABASE_URL`: Neon Postgres connection string
  - `OPENAI_API_KEY`: OpenAI API key
  - `PINECONE_API_KEY`: Pinecone API key
  - `PINECONE_ENVIRONMENT`: Pinecone environment
  - `PINECONE_INDEX_NAME`: Pinecone index name

### Config Classes
- Location: `src/thematic_lm/config.py`
- Use Pydantic `BaseSettings` for type-safe configuration
- Separate classes for different concerns (database, LLM, pipeline, API)
- Validate on startup; fail fast if required variables missing

## Module Boundaries

### Clear Separation of Concerns

#### Orchestration Layer (`orchestrator/`)
- LangGraph pipeline definitions (StateGraph, nodes, edges)
- State management (TypedDict or Pydantic models for typed state)
- Checkpoint configuration (PostgresSaver setup)
- No direct agent logic; delegates to `agents/` module

#### Agent Logic Layer (`agents/`)
- Coder, aggregator, reviewer, theme-coder, theme-aggregator implementations
- Prompt templates and LLM call wrappers
- Identity perspective handling
- No direct database or API access; receives state from orchestrator

#### Persistence Layer (`models/`)
- SQLAlchemy models for database tables
- Pydantic schemas for API request/response validation
- Database session management
- RLS policy enforcement via session variables

#### API Layer (`api/`)
- FastAPI routes and dependencies
- Request validation and error handling
- Authentication/authorization middleware
- BFF logic (translate user requests to pipeline jobs)
- No direct agent or orchestration logic; delegates to `orchestrator/`

#### Utilities Layer (`utils/`)
- Logging setup and structured logging helpers
- Cost estimation functions
- Codebook compression (LLMLingua integration)
- Quote ID encoding/decoding
- Shared helpers (no business logic)

## Contracts Storage

### Location
`.kiro/contracts/` for machine-readable schemas and human documentation

### Structure
```
.kiro/contracts/
├── api/                    # BFF API contracts
│   ├── openapi.yaml       # OpenAPI 3.0 spec
│   └── examples/          # JSON examples for validation
├── agents/                 # Agent input/output contracts
│   ├── coder.md           # Coder agent contract
│   ├── aggregator.md      # Aggregator agent contract
│   ├── reviewer.md        # Reviewer agent contract
│   └── theme-agents.md    # Theme coder/aggregator contracts
└── state/                  # LangGraph state schemas
    └── pipeline-state.md  # Typed state definitions
```

### Contract Versioning
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Document breaking changes in `.kiro/steering/multi-agent-protocols.md`
- Maintain deprecation calendar for contract changes
