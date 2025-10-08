# Testing Standards

## Test Pyramid Levels (v1 Relaxed)

### Unit Tests
- **Scope**: Pure logic with mocks; fast; no external dependencies
- **Location**: `tests/unit/`
- **Characteristics**:
  - Test individual functions, classes, or modules in isolation
  - Mock all external dependencies (database, APIs, file system)
  - Run in milliseconds; no I/O operations
  - Deterministic; no flakiness allowed
- **Coverage**: Focus on critical paths (agent logic, cost estimation, compression, quote ID encoding)
- **Example**: Test code aggregator merging logic with mocked LLM responses

### Contract Tests (Simplified for v1)

#### Provider Tests
- **Scope**: Validate BFF endpoints match OpenAPI spec examples
- **Location**: `tests/contract/`
- **Characteristics**:
  - Test that API routes return responses matching OpenAPI schema
  - Validate request/response structure, status codes, error envelopes
  - Mock downstream dependencies (pipeline, database)
  - Fast; no real LLM or database calls
- **Example**: POST /analyze returns 202 with `analysis_id` and `estimated_cost_usd`

#### Example Validation
- **Scope**: Validate JSON examples in `.kiro/contracts/**/examples/` against their schemas
- **Location**: `tests/contract/`
- **Characteristics**:
  - Load example files and validate against JSON schemas
  - Ensure examples stay in sync with schema changes
  - Fast; no external dependencies
- **Example**: Validate `coder-output-example.json` against coder output schema
- **Validation Script**: `scripts/validate_contracts.py` runs in CI to validate all contracts

#### Deferred to Post-v1
- Pydantic-to-JSON-Schema diff validation
- OpenAPI-to-FastAPI route validation (ensure all routes defined in spec exist in code)

### Integration Tests
- **Scope**: Real DB (Neon with RLS), Pinecone, OpenAI API calls
- **Location**: `tests/integration/`
- **Gating**: Only run when `LIVE_TESTS=1` and required API keys are set
- **Characteristics**:
  - Test interactions between components with real external services
  - Validate RLS policies, database queries, vector storage, LLM calls
  - Slower (seconds to minutes); incur API costs
  - Respect `COST_BUDGET_USD`; skip or fail tests that would exceed budget
- **Cost Estimation**: Every test that calls LLM APIs must estimate and log token usage
- **Example**: Test reviewer agent updating codebook with real database and embeddings

### E2E Smoke Tests
- **Scope**: Full pipeline with small dataset (5-10 interactions); validates entire flow
- **Location**: `tests/e2e/`
- **Gating**: Only run when `LIVE_TESTS=1` and required API keys are set
- **Characteristics**:
  - Test complete analysis workflow from API request to final themes
  - Use minimal data to keep costs low (<$0.50 per test)
  - Validate end-to-end integration of all components
  - Slowest (minutes); highest cost
- **Coverage**: Focus on one comprehensive smoke test for v1
- **Example**: Submit analysis request, poll for completion, validate themes structure

## Flake Policy

### Zero Tolerance for Flaky Tests
- Tests must be deterministic; no random failures allowed
- Retries allowed only for known transient failures (network timeouts, rate limits)
- Flaky tests are treated as failures; must be fixed or disabled

### Handling Transient Failures
- Network timeouts: Retry up to 2 times with exponential backoff
- Rate limits: Respect `Retry-After` header; skip test if limit exceeded
- Service unavailable: Retry once after 5 seconds; fail if still unavailable
- Log all retries with reason for debugging

### Debugging Flaky Tests
- Add detailed logging to identify failure cause
- Use `pytest-rerunfailures` plugin for automatic retry (max 2 reruns)
- Mark consistently flaky tests with `@pytest.mark.flaky` and create issue to fix

## Coverage Targets (Relaxed for v1)

### v1 Focus
- **E2E**: One comprehensive smoke test covering full pipeline
- **Unit**: Critical paths (agent logic, cost estimation, compression, quote ID encoding)
- **Integration**: RLS enforcement, codebook updates, theme generation
- **Contract**: All BFF endpoints match OpenAPI spec

### Deferred to Post-v1
- Strict percentage targets (e.g., 80% line coverage)
- Branch coverage analysis
- Mutation testing

## Live Test Gating

### Environment Variables
- `LIVE_TESTS=1`: Enable integration and E2E tests
- `COST_BUDGET_USD`: Maximum allowed cost for all live tests (default: 5.00)
- `DRY_RUN=1`: Simulate LLM calls without actual API requests (default in CI)

### CI/CD Strategy (v1)
- **Default**: Run unit and contract tests only (`LIVE_TESTS=0`, `DRY_RUN=1`)
- **Manual Trigger**: Run live tests manually for v1 (nightly CI deferred to post-v1)
- **Cost Tracking**: Log estimated and actual costs for all live test runs
- **Budget Enforcement**: Fail test suite if cumulative cost exceeds `COST_BUDGET_USD`

### Required API Keys
- `OPENAI_API_KEY`: Required for integration and E2E tests
- `PINECONE_API_KEY`: Required for integration tests with vector storage
- `DATABASE_URL`: Required for integration and E2E tests (Neon with RLS)

### Skip Logic
```python
import pytest
import os

@pytest.mark.skipif(
    os.getenv("LIVE_TESTS") != "1",
    reason="Live tests disabled (set LIVE_TESTS=1 to enable)"
)
def test_integration_with_real_llm():
    # Test code here
    pass
```

## Cost Estimation

### Token Usage Logging
Every test that calls LLM APIs must:
1. Estimate token usage before test execution
2. Log estimated cost at test start
3. Log actual token usage and cost at test end
4. Fail if actual cost exceeds estimate by >20%

### Example
```python
def test_coder_agent_with_real_llm():
    estimated_tokens = estimate_tokens(prompt, max_completion=500)
    estimated_cost = estimated_tokens * COST_PER_TOKEN
    logger.info(f"Estimated cost: ${estimated_cost:.4f}")
    
    # Run test
    result = coder_agent.code(interaction)
    
    actual_cost = result.usage.total_tokens * COST_PER_TOKEN
    logger.info(f"Actual cost: ${actual_cost:.4f}")
    
    assert actual_cost <= estimated_cost * 1.2, "Cost exceeded estimate by >20%"
```

## Test Organization

### Naming Conventions
- Unit tests: `test_<module>_<function>.py`
- Contract tests: `test_contract_<endpoint>.py`
- Integration tests: `test_integration_<component>.py`
- E2E tests: `test_e2e_<workflow>.py`

### Fixtures
- Location: `tests/conftest.py` for shared fixtures
- Use `pytest` fixtures for setup/teardown
- Scope fixtures appropriately (`function`, `module`, `session`)

### Markers
- `@pytest.mark.unit`: Unit tests (default; no marker needed)
- `@pytest.mark.contract`: Contract tests
- `@pytest.mark.integration`: Integration tests (requires `LIVE_TESTS=1`)
- `@pytest.mark.e2e`: E2E tests (requires `LIVE_TESTS=1`)
- `@pytest.mark.slow`: Slow tests (>5 seconds)
- `@pytest.mark.flaky`: Known flaky tests (to be fixed)

### Running Tests
```bash
# Unit and contract tests only (fast, no external dependencies)
pytest -m "not integration and not e2e"

# All tests including live tests
LIVE_TESTS=1 pytest

# E2E smoke test only
LIVE_TESTS=1 pytest -m e2e

# Verbose with cost logging
LIVE_TESTS=1 pytest -v --log-cli-level=INFO
```
