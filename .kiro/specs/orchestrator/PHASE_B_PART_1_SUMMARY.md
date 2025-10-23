# Phase B Part 1 Summary: Orchestrator Spec Amendments

## Overview

Phase B Part 1 inserts a simplified, executable coder-only pipeline into the orchestrator spec. This allows us to execute coder-agents first, then orchestrator second, without implementing the full aggregator/reviewer/theme pipeline.

## Changes Made

### 1. DEPENDENCIES.yaml

**Added**:
- `consumes_internal` section with `internal/agents-coder@v1` interface
- Required fields: `codes`, `token_usage`
- Note: "No dependency on cost-manager in Phase B Part 1"

**Updated**:
- Marked `code-aggregator`, `reviewer`, `theme-coder-agents`, `theme-aggregator` as "Deferred to Phase B Part 2+"
- Added note to `cost-manager`: "Not used in Phase B Part 1 (token usage only)"

### 2. requirements.md

**Requirement 3 (Agent Coordination)**:
- Added "Phase B Part 1 - Simplified" acceptance criteria
- Direct coder invocation via `internal/agents-coder@v1`
- Collect codes directly into `state["codes"]` (no aggregator/reviewer/theme)
- Identities loaded once at process start

**Requirement 8 (Cost Tracking)**:
- Added "Phase B Part 1 - Token Usage Only" acceptance criteria
- Track token usage only (prompt_tokens, completion_tokens)
- No cost calculation (deferred to Phase B Part 2+)

**Requirement 6 (Identity Configuration)**:
- Clarified: Identities loaded once at process start and reused

**Requirement 9 (Live Test Gating)**:
- Added Part 1 DRY_RUN behavior: "return mock codes end-to-end"
- Added Part 1 LIVE_TESTS behavior: "gate integration tests"

### 3. design.md

**Added Sections**:

1. **Phase B Part 1 Architecture (Simplified Path)**
   - Diagram: `[fetch_data] → [coder_node] → [complete]`
   - Other nodes present but not on Part 1 path
   - Scope: Fetch, chunk, fan-out coders, gather codes, track token usage
   - Deferred: Aggregator, reviewer, theme stages, cost calculation

2. **Phase B Part 1: Coder Node Implementation**
   - Load identities once at process start
   - Chunk interactions using models/chunking@v1
   - Fan-out coder calls per identity/chunk
   - Async execution with semaphore rate-limit (`max_parallel_llm_calls`)
   - Gather results into `state["codes"]`
   - Track token usage in `state["metadata"]["token_usage"]`
   - Code example showing semaphore pattern

3. **Configuration Knobs (Phase B Part 1)**
   - `DRY_RUN` (default: 1)
   - `LIVE_TESTS` (default: 0)
   - `max_parallel_llm_calls` (default: 5)
   - `chunk_max_tokens` (default: 500)
   - `IDENTITIES_PATH` (default: "identities.yaml")
   - Note: No pricing fields in Part 1

### 4. tasks.md

**Restructured with Three Phases**:

#### A. Infrastructure Setup (Phase A)
- Original tasks 1-7 (project setup, state schema, identities, checkpointer, graph structure, routing, fetch_data stub)
- Kept as-is or marked done if already complete

#### B. Phase B Part 1 — Execute Later (NEW)
Five new executable tasks:

- **ORCH-B1-001**: Update DEPENDENCIES.yaml to consume internal/agents-coder@v1
- **ORCH-B1-002**: Update requirements.md with Part 1 overlay
- **ORCH-B1-003**: Update design.md with coder_node details
- **ORCH-B1-004**: Replace placeholder coding step with coder_node for Part 1 execution path
- **ORCH-B1-005**: Add/confirm configuration knobs used by orchestrator

#### C. Phase B Part 2+ (Deferred)
- Original tasks 8-20 moved here
- Marked as "DEFERRED - Do Not Execute Yet"
- Includes: Full fetch_data, Send API, aggregator, reviewer, theme stages, cost calculation, error recovery, logging, E2E tests

## Phase B Part 1 Task List (Executable)

Execute these tasks AFTER coder-agents spec is complete:

### ORCH-B1-001: Update DEPENDENCIES.yaml
- Add `consumes_internal` section with internal/agents-coder@v1
- Document required fields: codes, token_usage
- Add note: "No dependency on cost-manager in Phase B Part 1"
- Update internal_dependencies to mark aggregator/reviewer/theme as deferred
- **Type**: Documentation only; no code changes

### ORCH-B1-002: Update requirements.md
- Under Requirement 3: Add Part 1 acceptance criteria for direct coder invocation
- Under Requirement 8: Add Part 1 acceptance criteria for token-usage-only
- Under Requirement 6: Clarify identities loaded once at process start
- Under Requirement 9: Add Part 1 DRY_RUN/LIVE_TESTS behavior
- **Type**: Documentation only; no code changes

### ORCH-B1-003: Update design.md
- Add "Phase B Part 1 Architecture" section with simplified graph
- Add "Phase B Part 1: Coder Node Implementation" section with:
  * Fan-out per identity/chunk logic
  * Semaphore rate-limit implementation
  * Gather to state["codes"] logic
  * Token usage tracking
- Add "Configuration Knobs (Phase B Part 1)" section
- **Type**: Documentation only; no code changes

### ORCH-B1-004: Implement coder_node
- Modify StateGraph to route: fetch_data → coder_node → complete
- Implement coder_node function:
  * Load identities once at module init
  * Chunk interactions using models/chunking@v1
  * Fan-out async calls to internal/agents-coder@v1 per identity/chunk
  * Apply semaphore rate-limit (max_parallel_llm_calls)
  * Gather codes into state["codes"]
  * Track token usage in state["metadata"]["token_usage"]
- Keep other nodes present but off the Part 1 route
- Write unit tests for coder_node logic
- **Type**: Core implementation; depends on internal/agents-coder@v1

### ORCH-B1-005: Add/confirm configuration knobs
- Document in config/settings.py or steering docs:
  * DRY_RUN (default: 1)
  * LIVE_TESTS (default: 0)
  * max_parallel_llm_calls (default: 5)
  * chunk_max_tokens (default: 500)
  * IDENTITIES_PATH (default: "identities.yaml")
- Note: No pricing fields in Part 1
- Add validation for required config values
- Write unit tests for config loading
- **Type**: Configuration; no API calls

## Execution Order

1. **Complete coder-agents spec** (all tasks in `.kiro/specs/coder-agents/tasks.md`)
2. **Execute ORCH-B1-001 through ORCH-B1-005** (in order)
3. **Validate Phase B Part 1** with integration tests
4. **Defer Phase B Part 2+** until Part 1 is stable

## What's Deferred

The following components are NOT implemented in Phase B Part 1:

- Code aggregation and deduplication
- Reviewer and codebook updates
- Theme generation (coder + aggregator)
- Cost calculation and budget enforcement
- PostgresSaver checkpointing (beyond basic state)
- Full error recovery and retry logic
- Comprehensive structured logging
- E2E tests for full pipeline

These will be implemented in Phase B Part 2+ after Part 1 is validated.

## Key Design Decisions

1. **Identities loaded once**: At process start, not per-job (performance optimization)
2. **Semaphore rate-limit**: Cap parallel LLM calls to avoid rate limits
3. **Token usage only**: No cost calculation in Part 1 (simpler implementation)
4. **Direct code collection**: Bypass aggregator/reviewer for faster iteration
5. **Deferred checkpointing**: Basic state only; full checkpointing in Part 2+

## Success Criteria

Phase B Part 1 is complete when:

1. All five ORCH-B1 tasks are executed and passing tests
2. Orchestrator can invoke internal/agents-coder@v1 for all identities
3. Codes are collected into state["codes"] correctly
4. Token usage is tracked in state["metadata"]["token_usage"]
5. DRY_RUN=1 returns mock codes end-to-end
6. LIVE_TESTS=1 gates integration tests correctly
7. Unit tests pass for coder_node logic
8. Configuration knobs are documented and validated

## Next Steps

After Phase B Part 1 is complete:

1. Review and validate coder_node implementation
2. Run integration tests with LIVE_TESTS=1
3. Measure token usage and performance
4. Plan Phase B Part 2+ (aggregator/reviewer/theme stages)
5. Implement cost calculation and budget enforcement
6. Add full checkpointing and error recovery
