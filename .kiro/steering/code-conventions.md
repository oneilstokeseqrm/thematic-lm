# Code Conventions

## Style

- **Formatter**: Black with max line length 100
- **Linter**: Ruff with default rules
- **Import Order**: isort compatible (stdlib, third-party, local)
- **Docstrings**: Google style for functions and classes

### Example
```python
"""Module for coder agent implementation."""

from typing import List

from pydantic import BaseModel

from thematic_lm.models import Code, Interaction


def generate_codes(interaction: Interaction) -> List[Code]:
    """Generate codes for a single interaction.
    
    Args:
        interaction: The interaction to code
        
    Returns:
        List of generated codes with quotes
        
    Raises:
        ValueError: If interaction text is empty
    """
    if not interaction.text:
        raise ValueError("Interaction text cannot be empty")
    # Implementation here
```

## Typing

### Full Type Hints Required
- All function signatures must include type hints
- Use `mypy` in strict mode
- No `Any` types unless absolutely necessary (document why)

### Structured Data
- Use `TypedDict` or Pydantic models for structured data
- Prefer Pydantic for validation and serialization
- Use `TypedDict` for simple state objects in LangGraph

### Example
```python
from typing import TypedDict, List
from pydantic import BaseModel, Field


# LangGraph state (TypedDict)
class PipelineState(TypedDict):
    account_id: str
    interactions: List[str]
    codes: List[dict]
    themes: List[dict]


# API schema (Pydantic)
class AnalysisRequest(BaseModel):
    account_id: str = Field(..., description="Account identifier")
    start_date: str = Field(..., description="Start date (ISO 8601)")
    end_date: str = Field(..., description="End date (ISO 8601)")
```

## Logging

### Structured JSON Logging

Required fields for all log entries:
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger`: Logger name (module path)
- `message`: Human-readable message
- `tenant_id`: Tenant identifier (if available)
- `analysis_id`: Analysis job ID (if in job context)
- `trace_id`: Request correlation ID

### Example
```python
import logging
import structlog

logger = structlog.get_logger(__name__)

def process_analysis(analysis_id: str, tenant_id: str):
    logger.info(
        "Starting analysis",
        analysis_id=analysis_id,
        tenant_id=tenant_id,
        trace_id=get_trace_id()
    )
    # Processing logic
    logger.info(
        "Analysis completed",
        analysis_id=analysis_id,
        tenant_id=tenant_id,
        codes_generated=87,
        themes_generated=12
    )
```

### Log Levels
- **DEBUG**: Detailed diagnostic info (opt-in only; may include content)
- **INFO**: General informational messages (no PII or raw content)
- **WARNING**: Unexpected but handled situations
- **ERROR**: Error conditions that don't stop execution
- **CRITICAL**: Severe errors requiring immediate attention

### Content Logging Rules
- Never log raw interaction text at INFO level
- Use DEBUG with explicit opt-in for content logging
- Scrub PII patterns before logging (emails, phone numbers)
- Log only metadata: IDs, counts, timestamps, status

## Identifiers

### UUIDs for Primary Keys
- Use UUIDs (uuid4) for all primary keys
- Generate in application code, not database
- Store as UUID type in Postgres (not string)

### Descriptive Prefixes in Logs
Use prefixes to clarify ID types in logs:
- `analysis_`: Analysis job IDs
- `code_`: Code IDs
- `theme_`: Theme IDs
- `interaction_`: Interaction IDs
- `account_`: Account/tenant IDs

### Example
```python
import uuid

analysis_id = uuid.uuid4()
logger.info(f"Created analysis: analysis_{analysis_id}")
```

## Error Handling

### Raise Specific Exceptions
- Use built-in exceptions where appropriate (`ValueError`, `TypeError`, etc.)
- Create custom exceptions for domain-specific errors
- Include context in error messages

### Example
```python
class CostLimitExceededError(Exception):
    """Raised when estimated cost exceeds budget."""
    
    def __init__(self, estimated_cost: float, budget: float):
        self.estimated_cost = estimated_cost
        self.budget = budget
        super().__init__(
            f"Estimated cost (${estimated_cost:.2f}) exceeds "
            f"budget limit (${budget:.2f})"
        )


def validate_cost(estimated_cost: float, budget: float):
    if estimated_cost > budget:
        raise CostLimitExceededError(estimated_cost, budget)
```

### Log at Appropriate Levels
- **ERROR**: Log exceptions with full traceback
- **WARNING**: Log handled errors or degraded functionality
- **INFO**: Log recovery actions or fallback behavior

### Include Context
- Log relevant IDs (analysis_id, tenant_id, trace_id)
- Include input parameters that led to error
- Suggest corrective actions in error messages

## Async Patterns

### Use async/await Consistently
- All I/O operations should be async (database, API calls, file I/O)
- Use `asyncio` for concurrency, not threads
- Avoid blocking calls in async contexts

### Example
```python
import asyncio
from typing import List

async def fetch_interactions(account_id: str) -> List[Interaction]:
    """Fetch interactions from database asynchronously."""
    async with get_db_session() as session:
        result = await session.execute(
            select(Interaction).where(Interaction.account_id == account_id)
        )
        return result.scalars().all()


async def process_batch(interactions: List[Interaction]) -> List[Code]:
    """Process interactions concurrently."""
    tasks = [code_interaction(i) for i in interactions]
    return await asyncio.gather(*tasks)
```

### Avoid Blocking Calls
- Use `asyncio.to_thread()` for CPU-bound work
- Use async libraries (aiohttp, asyncpg) instead of sync equivalents
- Never use `time.sleep()` in async code (use `asyncio.sleep()`)
