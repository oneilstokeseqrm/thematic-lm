---
spec_id: orchestrator
name: LangGraph Pipeline Orchestrator
version: 1.0.0
status: Draft
owners: ["@dev-team"]
provides:
  - internal/orchestration-pipeline@v1
consumes:
  - models/chunking@v1
  - models/quote_id@v1
  - models/codebook@v1
  - models/themes@v1
---

# Requirements: LangGraph Pipeline Orchestrator

## Introduction

The orchestrator coordinates the multi-agent thematic analysis pipeline using LangGraph. It manages job lifecycle, state transitions, checkpointing, and agent coordination across coding and theme development stages.

## Requirements

### Requirement 1: Pipeline Initialization

**User Story**: As a system operator, I want analysis jobs to initialize with proper configuration, so that the pipeline can execute with correct parameters.

#### Acceptance Criteria

1. WHEN an analysis job is submitted with account_id, start_date, and end_date, THE SYSTEM SHALL create a StateGraph instance with typed state containing interaction_ids, codes, themes, and metadata
2. WHEN the pipeline initializes, THE SYSTEM SHALL load identities.yaml from the configured path at process start (not per-job)
3. WHEN identities.yaml is missing or invalid, THE SYSTEM SHALL fail fast with a clear error message indicating the configuration issue
4. WHEN the pipeline initializes, THE SYSTEM SHALL configure PostgresSaver with the database connection for checkpoint persistence
5. WHEN the pipeline initializes, THE SYSTEM SHALL validate that all required environment variables (DATABASE_URL, OPENAI_API_KEY) are present

### Requirement 2: State Management

**User Story**: As a pipeline component, I want access to shared state, so that I can read inputs and write outputs for downstream stages.

#### Acceptance Criteria

1. WHEN a node function executes, THE SYSTEM SHALL provide typed state access via TypedDict with fields: account_id, interaction_ids, codes, themes, metadata, errors
2. WHEN a node function updates state, THE SYSTEM SHALL persist the update to the state object for downstream nodes
3. WHEN state exceeds 10MB, THE SYSTEM SHALL log a warning about potential performance impact
4. WHEN state contains sensitive data, THE SYSTEM SHALL ensure it is not logged at INFO level

### Requirement 3: Agent Coordination

**User Story**: As an orchestrator, I want to coordinate multiple agents in sequence and parallel, so that the analysis pipeline executes efficiently.

#### Acceptance Criteria

1. WHEN the coding stage begins, THE SYSTEM SHALL use Send API to spawn parallel coder agents (one per identity from identities.yaml)
2. WHEN all coder agents complete, THE SYSTEM SHALL invoke the code aggregator node with collected outputs
3. WHEN the code aggregator completes, THE SYSTEM SHALL invoke the reviewer node to update the codebook
4. WHEN the reviewer completes, THE SYSTEM SHALL transition to theme generation stage via conditional edge
5. WHEN the theme generation stage begins, THE SYSTEM SHALL spawn parallel theme-coder agents via Send API
6. WHEN all theme-coder agents complete, THE SYSTEM SHALL invoke the theme aggregator node to produce final themes

### Requirement 4: Checkpoint Persistence

**User Story**: As a system operator, I want pipeline state checkpointed at key stages, so that failed jobs can be resumed without reprocessing.

#### Acceptance Criteria

1. WHEN the coding stage completes, THE SYSTEM SHALL persist a checkpoint with analysis_id, stage="coding_complete", and updated codebook
2. WHEN the theme stage completes, THE SYSTEM SHALL persist a checkpoint with analysis_id, stage="theme_complete", and final themes
3. WHEN a checkpoint is created, THE SYSTEM SHALL include timestamps (created_at) and status (in_progress, completed, failed)
4. WHEN a job fails mid-execution, THE SYSTEM SHALL persist a checkpoint with error details for debugging
5. WHEN checkpoint persistence fails, THE SYSTEM SHALL log the error but not block pipeline execution (fail open)

### Requirement 5: Error Recovery

**User Story**: As a system operator, I want the pipeline to handle errors gracefully, so that transient failures don't cause complete job failure.

#### Acceptance Criteria

1. WHEN a single coder agent fails, THE SYSTEM SHALL log the error and continue with outputs from successful agents
2. WHEN the code aggregator fails, THE SYSTEM SHALL abort the job and persist a failed checkpoint with error details
3. WHEN the reviewer fails, THE SYSTEM SHALL abort the job and persist a failed checkpoint with error details
4. WHEN a theme-coder agent fails, THE SYSTEM SHALL log the error and continue with outputs from successful agents
5. WHEN the theme aggregator fails, THE SYSTEM SHALL abort the job and persist a failed checkpoint with error details
6. WHEN an LLM API call fails with a retriable error (timeout, 5xx), THE SYSTEM SHALL retry up to 3 times with exponential backoff before failing

### Requirement 6: Identity Configuration

**User Story**: As a researcher, I want to configure multiple coder identities, so that the analysis captures diverse perspectives.

#### Acceptance Criteria

1. WHEN the process starts, THE SYSTEM SHALL load identities.yaml and parse identity definitions (id, name, description, prompt_prefix)
2. WHEN identities.yaml contains invalid YAML, THE SYSTEM SHALL fail fast with a parse error
3. WHEN identities.yaml contains no identities, THE SYSTEM SHALL fail fast with a validation error
4. WHEN identities.yaml is loaded, THE SYSTEM SHALL make identity list accessible to coder agent nodes
5. WHEN an identity has a missing required field (id, name, prompt_prefix), THE SYSTEM SHALL fail fast with a validation error

### Requirement 7: Conditional Routing

**User Story**: As an orchestrator, I want to route between stages based on state, so that the pipeline can adapt to different scenarios.

#### Acceptance Criteria

1. WHEN the reviewer completes and codebook has >0 codes, THE SYSTEM SHALL route to theme generation stage
2. WHEN the reviewer completes and codebook has 0 codes, THE SYSTEM SHALL route to completion with empty themes
3. WHEN any stage fails with a non-retriable error, THE SYSTEM SHALL route to failure handling node
4. WHEN the theme aggregator completes, THE SYSTEM SHALL route to completion node

### Requirement 8: Cost Tracking

**User Story**: As a system operator, I want to track actual costs during execution, so that I can compare against estimates.

#### Acceptance Criteria

1. WHEN each LLM call completes, THE SYSTEM SHALL record token usage (prompt_tokens, completion_tokens) in state metadata
2. WHEN the job completes, THE SYSTEM SHALL calculate total cost (sum of all LLM calls) and include in final checkpoint
3. WHEN actual cost exceeds estimate by >20%, THE SYSTEM SHALL log a warning for cost monitoring

### Requirement 9: Live Test Gating

**User Story**: As a developer, I want integration tests to respect LIVE_TESTS flag, so that I can run tests without incurring API costs.

#### Acceptance Criteria

1. WHEN LIVE_TESTS=0, THE SYSTEM SHALL use mock LLM responses in test mode
2. WHEN LIVE_TESTS=1, THE SYSTEM SHALL use real LLM API calls in test mode
3. WHEN DRY_RUN=1, THE SYSTEM SHALL simulate LLM calls without actual API requests (return mock responses)

### Requirement 10: Observability Integration

**User Story**: As a system operator, I want structured logs for all pipeline events, so that I can debug issues and monitor performance.

#### Acceptance Criteria

1. WHEN the pipeline starts, THE SYSTEM SHALL log with fields: analysis_id, account_id, tenant_id, stage="started", timestamp
2. WHEN each stage completes, THE SYSTEM SHALL log with fields: analysis_id, stage, duration_ms, timestamp
3. WHEN the pipeline completes, THE SYSTEM SHALL log with fields: analysis_id, status="completed", total_duration_ms, codes_generated, themes_generated, timestamp
4. WHEN the pipeline fails, THE SYSTEM SHALL log with fields: analysis_id, status="failed", error_code, error_message, timestamp
5. WHEN logging, THE SYSTEM SHALL never include raw interaction text at INFO level (use DEBUG with opt-in)
