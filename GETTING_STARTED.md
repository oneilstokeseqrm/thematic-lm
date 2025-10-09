# Getting Started with Thematic-LM

## Phase A Complete! 🎉

The foundational project structure is now in place. Here's how to get started.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** (3.12 recommended)
- **uv** or **poetry** for dependency management
- **PostgreSQL database** (Neon recommended for development)
- **OpenAI API key**
- **Pinecone account** (API key, environment, index name)

## Quick Start

### 1. Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Or using poetry:
```bash
poetry install
```

Or using pip:
```bash
pip install -e .
```

### 2. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```bash
# Database (use Neon or local PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@host/database

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Pinecone
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=your-environment
PINECONE_INDEX_NAME=thematic-codes

# Optional: Adjust these defaults
COST_BUDGET_USD=5.00
DRY_RUN=1
LOG_LEVEL=INFO
```

### 3. Initialize Database

Run Alembic migrations to create the database schema:
```bash
alembic upgrade head
```

This creates:
- `analyses` table (job metadata)
- `analysis_checkpoints` table (pipeline state)

### 4. Customize Identities (Optional)

The `identities.yaml` file contains example identity perspectives for the coder agents. You can customize these or add more:

```yaml
identities:
  - id: analyst
    name: "Analytical Perspective"
    prompt_prefix: |
      You are an analytical researcher...
  
  - id: empathetic
    name: "Empathetic Perspective"
    prompt_prefix: |
      You are an empathetic listener...
```

### 5. Start the API

```bash
uvicorn src.thematic_lm.api.main:app --reload
```

The API will be available at `http://localhost:8000`

### 6. Test the API

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Submit Analysis Request:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{
    "account_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }'
```

**Check Analysis Status:**
```bash
curl http://localhost:8000/analysis/{analysis_id} \
  -H "Authorization: Bearer test-token"
```

## Running Tests

### Unit Tests (No External Dependencies)

```bash
pytest tests/unit/ -v
```

### Integration Tests (Requires Database)

```bash
LIVE_TESTS=1 pytest tests/integration/ -v
```

### All Tests

```bash
pytest -v
```

## Project Structure

```
thematic-lm/
├── src/thematic_lm/          # Application code
│   ├── api/                  # FastAPI BFF layer
│   │   ├── main.py          # FastAPI app
│   │   ├── routes.py        # API endpoints
│   │   ├── middleware.py    # Request ID middleware
│   │   └── dependencies.py  # Auth & DB dependencies
│   ├── orchestrator/         # LangGraph pipeline
│   │   ├── graph.py         # StateGraph definition
│   │   ├── nodes.py         # Node functions
│   │   └── state.py         # State schema
│   ├── models/               # Database models
│   │   └── database.py      # SQLAlchemy models
│   ├── config/               # Configuration
│   │   └── settings.py      # Pydantic settings
│   └── utils/                # Utilities
│       └── logging.py       # Structured logging
├── tests/                    # Tests
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── alembic/                  # Database migrations
├── scripts/                  # Development scripts
├── .env.example             # Environment template
├── identities.yaml          # Identity configurations
└── pyproject.toml           # Project dependencies
```

## What's Working (Phase A)

✅ **API Endpoints:**
- `GET /health` - Health check
- `POST /analyze` - Submit analysis (returns 202)
- `GET /analysis/{id}` - Poll for status

✅ **Features:**
- Request ID tracking
- Idempotency support (24-hour window)
- Cost validation
- Date range validation
- Structured JSON logging
- Async database operations

✅ **Infrastructure:**
- SQLAlchemy models with async support
- Alembic migrations
- LangGraph pipeline scaffold
- Configuration management
- Unit and integration tests

## What's Not Working Yet (Phase B)

❌ **Agent Implementations:**
- Coder agents (placeholder)
- Aggregator agents (placeholder)
- Reviewer agent (placeholder)
- Theme agents (placeholder)

❌ **Pipeline Execution:**
- Orchestrator not triggered from API
- No actual LLM calls
- No checkpointing configured

❌ **Results:**
- Status endpoint returns minimal data
- No results retrieval

❌ **Authentication:**
- Placeholder accepts any Bearer token

## Development Workflow

### Making Code Changes

1. Make your changes in `src/thematic_lm/`
2. Run tests: `pytest tests/unit/`
3. Check types: `mypy src/`
4. Format code: `ruff format .`
5. Lint code: `ruff check .`

### Creating Database Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description"

# Review the generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Adding New Dependencies

Using uv:
```bash
uv add package-name
```

Using poetry:
```bash
poetry add package-name
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'thematic_lm'`:
- Install the package in editable mode: `pip install -e .` or `uv pip install -e .`
- This allows imports like `from thematic_lm.config import Settings`
- Without installation, use: `PYTHONPATH=. python ...` and import as `from src.thematic_lm.config import Settings`

**Note:** Tests use `from src.thematic_lm...` imports to work without installation.

### Database Connection Errors

If you see database connection errors:
- Verify `DATABASE_URL` in `.env` is correct
- Ensure it uses `postgresql+asyncpg://` (not just `postgresql://`)
- Check that your database is running and accessible
- Run migrations: `alembic upgrade head`

### API Startup Errors

If the API fails to start:
- Check that `identities.yaml` exists and is valid
- Verify all required environment variables are set
- Check logs for specific error messages

## Next Steps

Ready to implement Phase B? Here's what's next:

1. **Agent Implementations** - Implement the actual agent logic
2. **Checkpointing** - Configure PostgresSaver for state persistence
3. **Cost Estimation** - Implement token counting and cost calculation
4. **Pipeline Execution** - Wire up orchestrator to API
5. **Results Retrieval** - Store and return analysis results

See `PHASE_A_COMPLETE.md` for detailed Phase B priorities.

## Documentation

- **API Standards**: `.kiro/steering/api-standards.md`
- **Code Conventions**: `.kiro/steering/code-conventions.md`
- **Testing Standards**: `.kiro/steering/testing-standards.md`
- **Security Policies**: `.kiro/steering/security-policies.md`
- **Technical Architecture**: `.kiro/steering/tech.md`

## Getting Help

- Check the steering docs in `.kiro/steering/`
- Review the contracts in `.kiro/contracts/`
- Look at the specs in `.kiro/specs/`
- Read the Phase A completion summary in `PHASE_A_COMPLETE.md`

---

**Phase A is complete!** The foundation is solid. Time to build the agents! 🚀
