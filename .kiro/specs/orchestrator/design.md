# Design: LangGraph Pipeline Orchestrator

## Architecture Overview

The orchestrator is the central coordinator for the thematic analysis pipeline. It uses LangGraph's StateGraph to define a directed graph of agent nodes with typed state, conditional edges for routing, and PostgresSaver for checkpoint persistence.

### Long-term Architecture (Full Pipeline)

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              StateGraph                             │    │
│  │                                                      │    │
│  │  [Start] → [Fetch Data] → [Coder Agents (Send)]   │    │
│  │              ↓                    ↓                  │    │
│  │         [Aggregator] → [Reviewer] → [Theme Coders] │    │
│  │              ↓                           ↓           │    │
│  │         [Theme Aggregator] → [Complete]             │    │
│  │              ↓                                       │    │
│  │         [Persist Results]                           │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  PostgresSaver (Checkpoints) ←→ Database                   │
│  Identities Config ←→ identities.yaml                      │
└─────────────────────────────────────────────────────────────┘
```

### Phase B Part 1 Architecture (Simplified Path)

```
┌─────────────────────────────────────────────────────────────┐
│                Orchestrator (Phase B Part 1)                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │              StateGraph                             │    │
│  │                                                      │    │
│  │  [Start] → [Fetch Data] → [Coder Node]            │    │
│  │                              ↓                       │    │
│  │                          [Complete]                  │    │
│  │                                                      │    │
│  │  Other nodes present but not on Part 1 path:       │    │
│  │  [Aggregator], [Reviewer], [Theme Coders],         │    │
│  │  [Theme Aggregator] - all deferred                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Identities loaded once at process start                    │
│  Token usage tracked (no cost calculation in Part 1)        │
│  Semaphore rate-limit: max_parallel_llm_calls               │
└─────────────────────────────────────────────────────────────┘
```

**Phase B Part 1 Scope**:
- Fetch interactions from database
- Chunk interactions using models/chunking@v1
- Fan-out coder calls per identity/chunk (via internal/agents-coder@v1)
- Gather codes directly into state["codes"]
- Track token usage only (no cost calculation)
- Complete job with codes output

**Deferred to Phase B Part 2+**:
- Code aggregation and deduplication
- Reviewer and codebook updates
- Theme generation (coder + aggregator)
- Cost calculation and budget enforcement
- PostgresSaver checkpointing (beyond basic state)

## Phase B Part 1: Coder Node Implementation

### Coder Node Design

The `coder_node` is the core Phase B Part 1 implementation that:

1. **Loads identities once** at process start via `src.thematic_lm.utils.identities.load_identities()`
2. **Chunks interactions** using models/chunking@v1 contract (tiktoken cl100k_base, max tokens per chunk)
3. **Fan-out coder calls** per identity/chunk combination:
   - For each interaction: chunk into segments
   - For each chunk: invoke internal/agents-coder@v1 for each identity
   - Async execution with semaphore rate-limit (`max_parallel_llm_calls`)
4. **Gathers results** into state["codes"] (flat list of all codes from all identities/chunks)
5. **Tracks token usage** in state["metadata"]["token_usage"] (prompt_tokens, completion_tokens per call)

### Rate Limiting with Semaphore

```python
import asyncio
from typing import List, Dict

async def coder_node(state: AnalysisState, config: Dict) -> AnalysisState:
    """Execute coder agents for all identities and chunks."""
    max_parallel = config.get("max_parallel_llm_calls", 5)
    semaphore = asyncio.Semaphore(max_parallel)
    
    # Load identities (already loaded at module init)
    identities = IDENTITIES
    
    # Chunk all interactions
    chunks = []
    for interaction in state["interactions"]:
        interaction_chunks = chunk_text(
            interaction["text"],
            max_tokens=config.get("chunk_max_tokens", 500)
        )
        chunks.extend([
            {
                "interaction_id": interaction["id"],
                "chunk_index": idx,
                "text": chunk["text"],
                "start_pos": chunk["start_pos"],
                "end_pos": chunk["end_pos"]
            }
            for idx, chunk in enumerate(interaction_chunks)
        ])
    
    # Fan-out coder calls per identity/chunk
    async def call_coder_with_limit(identity, chunk):
        async with semaphore:
            return await invoke_coder_agent(identity, chunk, config)
    
    tasks = [
        call_coder_with_limit(identity, chunk)
        for identity in identities
        for chunk in chunks
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Collect codes and token usage
    all_codes = []
    token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
    
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Coder agent failed: {result}")
            continue
        
        all_codes.extend(result["codes"])
        token_usage["prompt_tokens"] += result["token_usage"]["prompt_tokens"]
        token_usage["completion_tokens"] += result["token_usage"]["completion_tokens"]
    
    return {
        **state,
        "codes": all_codes,
        "metadata": {
            **state.get("metadata", {}),
            "token_usage": token_usage
        },
        "current_stage": "complete"
    }
```

### Configuration Knobs (Phase B Part 1)

Settings used by orchestrator (documented in config/settings.py or .env):

- `DRY_RUN` (default: 1): Simulate LLM calls without actual API requests
- `LIVE_TESTS` (default: 0): Gate integration tests that call real APIs
- `max_parallel_llm_calls` (default: 5): Max concurrent LLM calls (semaphore limit)
- `chunk_max_tokens` (default: 500): Max tokens per chunk (models/chunking@v1)
- `IDENTITIES_PATH` (default: "identities.yaml"): Path to identities configuration

**Not used in Phase B Part 1** (deferred to Part 2+):
- Pricing fields (cost per token, budget limits)
- Checkpoint retention policies
- Aggregator/reviewer/theme configuration

## Key Classes/Functions

### AnalysisState (TypedDict)

Typed state shared across all nodes:

```python
from typing import TypedDict, List, Dict, Optional

class AnalysisState(TypedDict):
    # Job metadata
    analysis_id: str  # UUID
    account_id: str  # UUID
    tenant_id: str  # UUID
    start_date: str  # ISO 8601
    end_date: str  # ISO 8601
    
    # Data
    interaction_ids: List[str]  # UUIDs of interactions to process
    interactions: List[Dict]  # Full interaction objects with text
    
    # Outputs
    codes: List[Dict]  # Codes from aggregator
    codebook_version: Optional[str]  # e.g., "v42"
    themes: List[Dict]  # Final themes from theme aggregator
    
    # Metadata
    metadata: Dict  # Token usage, costs, timings
    errors: List[Dict]  # Error log for partial failures
    
    # Stage tracking
    current_stage: str  # "coding", "review", "theming", "complete"
```

### AnalysisOrchestrator

Main orchestrator class:

```python
from src.thematic_lm.utils.identities import load_identities, Identity

# Load identities once at module initialization
IDENTITIES = load_identities("identities.yaml")

class AnalysisOrchestrator:
    def __init__(
        self,
        db_uri: str
    ):
        self.identities = IDENTITIES
        self.checkpointer = PostgresSaver.from_conn_string(db_uri)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph StateGraph with nodes and edges."""
        graph = StateGraph(AnalysisState)
        
        # Add nodes
        graph.add_node("fetch_data", self.fetch_data_node)
        graph.add_node("code_aggregator", self.code_aggregator_node)
        graph.add_node("reviewer", self.reviewer_node)
        graph.add_node("theme_aggregator", self.theme_aggregator_node)
        graph.add_node("complete", self.complete_node)
        
        # Add edges
        graph.set_entry_point("fetch_data")
        graph.add_edge("fetch_data", "code_aggregator")
        graph.add_edge("code_aggregator", "reviewer")
        graph.add_conditional_edges(
            "reviewer",
            self.should_generate_themes,
            {
                "generate_themes": "theme_aggregator",
                "skip_themes": "complete"
            }
        )
        graph.add_edge("theme_aggregator", "complete")
        graph.set_finish_point("complete")
        
        return graph.compile(checkpointer=self.checkpointer)
    
    async def run(
        self,
        account_id: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """Execute analysis pipeline."""
        analysis_id = str(uuid.uuid4())
        
        initial_state = AnalysisState(
            analysis_id=analysis_id,
            account_id=account_id,
            tenant_id=get_tenant_id(account_id),
            start_date=start_date,
            end_date=end_date,
            interaction_ids=[],
            interactions=[],
            codes=[],
            codebook_version=None,
            themes=[],
            metadata={},
            errors=[],
            current_stage="started"
        )
        
        result = await self.graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": analysis_id}}
        )
        
        return result
```

### Node Functions

Each node is an async function that receives state and returns updated state:

```python
async def fetch_data_node(state: AnalysisState) -> AnalysisState:
    """Fetch interactions from database."""
    interactions = await fetch_interactions(
        account_id=state["account_id"],
        start_date=state["start_date"],
        end_date=state["end_date"]
    )
    
    return {
        **state,
        "interactions": interactions,
        "interaction_ids": [i["id"] for i in interactions],
        "current_stage": "coding"
    }

async def code_aggregator_node(state: AnalysisState) -> AnalysisState:
    """Aggregate codes from parallel coder agents."""
    # Spawn coder agents via Send API
    coder_tasks = [
        Send("coder_agent", {
            **state,
            "identity": identity
        })
        for identity in self.identities
    ]
    
    # Collect results
    coder_outputs = await gather_send_results(coder_tasks)
    
    # Aggregate codes
    aggregated_codes = aggregate_codes(coder_outputs)
    
    return {
        **state,
        "codes": aggregated_codes,
        "current_stage": "review"
    }
```

## LangGraph Specifics

### StateGraph Structure

- **Nodes**: Represent agent functions (coder, aggregator, reviewer, theme agents)
- **Edges**: Define execution flow (sequential or conditional)
- **State**: Typed dictionary shared across all nodes
- **Checkpointer**: PostgresSaver for persistence

### Send API for Parallelization

Use `Send` to spawn multiple agents in parallel:

```python
from langgraph.types import Send

# Spawn parallel coder agents (one per identity)
coder_tasks = [
    Send("coder_agent", {
        **state,
        "identity": identity,
        "interactions": state["interactions"]
    })
    for identity in identities
]
```

### Conditional Edges

Route based on state:

```python
def should_generate_themes(state: AnalysisState) -> str:
    """Decide whether to generate themes."""
    if len(state["codes"]) == 0:
        return "skip_themes"
    return "generate_themes"

graph.add_conditional_edges(
    "reviewer",
    should_generate_themes,
    {
        "generate_themes": "theme_aggregator",
        "skip_themes": "complete"
    }
)
```

## Database Schema References

### analysis_jobs Table

```sql
CREATE TABLE analysis_jobs (
    analysis_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, in_progress, completed, failed
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    estimated_cost_usd DECIMAL(10, 2),
    actual_cost_usd DECIMAL(10, 2),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    error_code VARCHAR(100),
    error_message TEXT
);

-- RLS policy
CREATE POLICY tenant_isolation ON analysis_jobs
    FOR SELECT USING (account_id = current_setting('app.current_account_id')::uuid);
```

### analysis_checkpoints Table

Managed by PostgresSaver (LangGraph):

```sql
CREATE TABLE analysis_checkpoints (
    thread_id VARCHAR(255) NOT NULL,  -- analysis_id
    checkpoint_id VARCHAR(255) NOT NULL,
    parent_checkpoint_id VARCHAR(255),
    checkpoint JSONB NOT NULL,  -- Serialized state
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (thread_id, checkpoint_id)
);
```

## External API Integrations

### LLM Providers (OpenAI)

- **Model**: GPT-4o for all agents
- **API**: OpenAI Python SDK
- **Rate Limiting**: Handled by cost-manager component
- **Retry**: Exponential backoff (max 3 retries)

### Database (Neon Postgres)

- **Connection**: Via DATABASE_URL environment variable
- **RLS**: Set `app.current_account_id` session variable
- **Role**: Use `app_user` for user-facing queries, `db_service` for checkpoints

## Identities Configuration

### Shared Identity Loader

The orchestrator consumes the shared identity loader from `src.thematic_lm.utils.identities`:

```python
from src.thematic_lm.utils.identities import load_identities, Identity

# Load once at module initialization
IDENTITIES = load_identities("identities.yaml")
```

**Note**: The orchestrator consumes the shared loader and only surfaces its validation errors; it does not re-implement identity parsing.

The shared loader validates:
- **Required fields**: `id`, `name`, `prompt_prefix`
- **Optional fields**: `description`

### Error Handling

The orchestrator surfaces validation errors from the shared loader:

```python
try:
    identities = load_identities("identities.yaml")
except ValueError as e:
    # Surface validation errors (missing required fields, no identities, etc.)
    logger.error(f"Identity configuration error: {e}")
    raise
except FileNotFoundError as e:
    # Surface file not found errors
    logger.error(f"Identity file not found: {e}")
    raise
except yaml.YAMLError as e:
    # Surface YAML parsing errors
    logger.error(f"Invalid YAML in identities file: {e}")
    raise
```

### identities.yaml Format

See `src.thematic_lm.utils.identities` for the canonical schema and validation logic.

Example format:
```yaml
identities:
  - id: "objective-analyst"
    name: "Objective Analyst"
    description: "Neutral, fact-focused perspective"  # OPTIONAL
    prompt_prefix: "You are an objective analyst focused on factual observations..."
  
  - id: "empathy-focused"
    name: "Empathy-Focused Researcher"
    # description field omitted - this is valid
    prompt_prefix: "You are an empathetic researcher focused on human experiences..."
```

## Dependencies

### Consumes

- **models/chunking@v1**: For chunking long interactions before coding
- **models/quote_id@v1**: For encoding quote IDs in coder outputs
- **models/codebook@v1**: For loading existing codebook and updating with new codes
- **models/themes@v1**: For producing final theme output

### Provides

- **internal/orchestration-pipeline@v1**: Pipeline execution and job lifecycle management

## Error Handling

### Failure Modes

1. **Identity Configuration Error**: Fail fast at process start if identities.yaml is invalid
2. **Database Connection Error**: Fail fast at process start if DATABASE_URL is invalid
3. **Coder Agent Failure**: Log error, continue with successful agents (graceful degradation)
4. **Aggregator/Reviewer Failure**: Abort job, persist failed checkpoint
5. **Theme Agent Failure**: Log error, continue with successful agents
6. **Checkpoint Persistence Failure**: Log error, continue execution (fail open)

### Recovery Strategies

- **Transient LLM Errors**: Retry up to 3 times with exponential backoff
- **Partial Agent Failures**: Continue with successful outputs if ≥1 agent succeeds
- **Critical Failures**: Persist checkpoint with error details for debugging
- **Resume from Checkpoint**: Load last checkpoint and retry failed stage (manual intervention)

## Performance Considerations

- **Parallel Execution**: Use Send API to spawn multiple agents concurrently
- **State Size**: Warn if state exceeds 10MB (potential performance impact)
- **Checkpoint Frequency**: Balance between recovery granularity and overhead
- **Database Connections**: Use connection pooling for PostgresSaver
