# Design: LangGraph Pipeline Orchestrator

## Architecture Overview

The orchestrator is the central coordinator for the thematic analysis pipeline. It uses LangGraph's StateGraph to define a directed graph of agent nodes with typed state, conditional edges for routing, and PostgresSaver for checkpoint persistence.

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
class AnalysisOrchestrator:
    def __init__(
        self,
        db_uri: str,
        identities_path: str = "identities.yaml"
    ):
        self.identities = self._load_identities(identities_path)
        self.checkpointer = PostgresSaver.from_conn_string(db_uri)
        self.graph = self._build_graph()
    
    def _load_identities(self, path: str) -> List[Identity]:
        """Load and validate identities from YAML."""
        # Validate required fields: id, name, prompt_prefix
        # Fail fast if invalid
    
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

### identities.yaml Format

```yaml
identities:
  - id: "objective-analyst"
    name: "Objective Analyst"
    description: "Neutral, fact-focused perspective"
    prompt_prefix: "You are an objective analyst focused on factual observations..."
  
  - id: "empathy-focused"
    name: "Empathy-Focused Researcher"
    description: "Human-centered, emotional perspective"
    prompt_prefix: "You are an empathetic researcher focused on human experiences..."
```

### Loading at Process Start

```python
# Load once at module initialization
IDENTITIES = load_identities("identities.yaml")

def load_identities(path: str) -> List[Identity]:
    with open(path) as f:
        config = yaml.safe_load(f)
    
    identities = []
    for item in config["identities"]:
        # Validate required fields
        if not all(k in item for k in ["id", "name", "prompt_prefix"]):
            raise ValueError(f"Invalid identity: {item}")
        
        identities.append(Identity(**item))
    
    if not identities:
        raise ValueError("No identities defined in identities.yaml")
    
    return identities
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
