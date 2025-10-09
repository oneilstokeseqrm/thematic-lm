# Thematic-LM

Multi-agent LLM system for automated thematic analysis of unstructured text data.

## Prerequisites

- Python 3.11+
- uv (or poetry)
- PostgreSQL (Neon recommended)
- OpenAI API key
- Pinecone account

## Quick Start

1. Clone and setup:

```bash
git clone <repo>
cd thematic-lm
./scripts/setup_dev.sh
```

2. Configure .env with your API keys:

```bash
# Copy from .env.example and fill in your keys
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...
PINECONE_INDEX_NAME=thematic-codes
```

3. Start the API:

```bash
uvicorn src.thematic_lm.api.main:app --reload
```

4. Test the API:

```bash
# Health check
curl http://localhost:8000/health

# Submit analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "account_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'

# Check analysis status
curl http://localhost:8000/analysis/{analysis_id} \
  -H "Authorization: Bearer test-token"
```

## Project Structure

```
.kiro/              - Specifications, contracts, steering docs
src/thematic_lm/    - Application code
  ├── api/          - FastAPI BFF layer
  ├── orchestrator/ - LangGraph pipeline
  ├── models/       - Database models
  ├── config/       - Configuration
  └── utils/        - Utilities
tests/              - Unit and integration tests
scripts/            - Development and deployment scripts
alembic/            - Database migrations
```

## Testing

```bash
# Unit tests only
pytest tests/unit/

# Integration tests (requires API keys)
LIVE_TESTS=1 pytest tests/integration/

# All tests with verbose output
pytest -v
```

## Development

### Running Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy src/
```

## Documentation

See `.kiro/steering/` for architectural documentation and standards:

- `product.md` - Product overview and capabilities
- `tech.md` - Technical architecture
- `structure.md` - Project structure
- `api-standards.md` - API design standards
- `testing-standards.md` - Testing strategy
- `security-policies.md` - Security and privacy
- `code-conventions.md` - Code style and conventions
- `multi-agent-protocols.md` - Contract versioning

## Phase A Status

✅ **Completed:**
- Project structure and configuration
- FastAPI BFF with request ID tracking
- Database models and migrations
- LangGraph orchestrator scaffold
- Basic unit and integration tests
- Development environment setup

🚧 **TODO (Phase B):**
- Agent implementations (coder, aggregator, reviewer, theme agents)
- PostgresSaver checkpointing
- Cost estimation logic
- Identity perspective handling
- Results retrieval

## License

[Your License Here]
