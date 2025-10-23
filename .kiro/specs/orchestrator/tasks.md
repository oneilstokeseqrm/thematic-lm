# Implementation Tasks: LangGraph Pipeline Orchestrator

## Task Organization

This task list is organized into three phases:

- **Phase A**: Infrastructure setup (completed or in progress)
- **Phase B Part 1**: Execute later - Simplified coder-only pipeline (NEW - execute before other orchestrator tasks)
- **Phase B Part 2+**: Deferred - Full pipeline with aggregator/reviewer/theme stages

## A. Infrastructure Setup (Phase A)

- [ ] 1. Set up project structure and dependencies
  - Install LangGraph, PostgresSaver, tiktoken, PyYAML
  - Create `src/thematic_lm/orchestrator/` module
  - Add type stubs for LangGraph if needed
  - _Requirements: ORCH-REQ-001_
  - _Note: No API calls; local setup only_

- [ ] 2. Define typed state schema
  - Create `AnalysisState` TypedDict with all required fields
  - Add validation helpers for state structure
  - Write unit tests for state validation
  - _Requirements: ORCH-REQ-002_
  - _Note: Pure Python; no external dependencies_

- [ ] 3. Consume shared identity loader
  - Import `load_identities` and `Identity` from `src.thematic_lm.utils.identities`
  - Call shared loader at module initialization with configured path
  - Add error handling to surface validation errors (ValueError, FileNotFoundError, yaml.YAMLError)
  - Write unit tests that verify orchestrator surfaces loader errors correctly
  - _Requirements: ORCH-REQ-006_
  - _Note: Depends on shared loader in utils; no API calls_

- [ ] 4. Create identities.yaml stub file
  - If identities.yaml already exists, do not overwrite; only append doc comments if missing
  - Generate `identities.yaml` with 2-3 example identities if file does not exist
  - Include: objective-analyst, empathy-focused, critical-thinker
  - Document format with required fields (id, name, prompt_prefix) and optional field (description) in comments
  - Show examples both with and without description field
  - _Requirements: ORCH-REQ-006_
  - _Note: Configuration file; no code_

- [ ] 5. Implement PostgresSaver checkpoint configuration
  - Configure PostgresSaver with DATABASE_URL
  - Test checkpoint persistence with mock state
  - Add error handling for connection failures
  - Write integration test (requires LIVE_TESTS=1 for real DB)
  - _Requirements: ORCH-REQ-004_
  - _Note: Requires database connection; gate with LIVE_TESTS=1_

- [ ] 6. Build StateGraph with placeholder nodes
  - Create `AnalysisOrchestrator` class
  - Define placeholder node functions (return state unchanged)
  - Add nodes: fetch_data, code_aggregator, reviewer, theme_aggregator, complete
  - Add sequential edges between nodes
  - _Requirements: ORCH-REQ-001, ORCH-REQ-003_
  - _Note: No LLM calls; structure only_

- [ ] 7. Add conditional routing logic
  - Implement `should_generate_themes(state)` function
  - Add conditional edge from reviewer to theme_aggregator or complete
  - Test routing with different state scenarios (0 codes, >0 codes)
  - _Requirements: ORCH-REQ-007_
  - _Note: Pure logic; no API calls_

- [ ] 8. Implement fetch_data_node
  - Query database for interactions in date range
  - Apply RLS (set app.current_account_id session variable)
  - Chunk interactions using models/chunking@v1 logic
  - Update state with interactions and interaction_ids
  - Write integration test (requires LIVE_TESTS=1 for real DB)
  - _Requirements: ORCH-REQ-001, ORCH-REQ-002_
  - _Note: Requires database; gate with LIVE_TESTS=1_

- [ ] 9. Implement Send API for parallel coder agents
  - Create Send tasks for each identity in identities list
  - Pass state + identity to each coder agent node
  - Collect outputs from all coder agents
  - Handle partial failures (log errors, continue with successes)
  - _Requirements: ORCH-REQ-003, ORCH-REQ-005_
  - _Note: No LLM calls yet; use mock coder responses_

- [ ] 10. Integrate code_aggregator_node
  - Call code-aggregator component with coder outputs
  - Update state with aggregated codes
  - Add error handling for aggregator failures
  - _Requirements: ORCH-REQ-003_
  - _Note: Depends on code-aggregator component_

- [ ] 11. Integrate reviewer_node
  - Call reviewer component with aggregated codes
  - Update state with codebook_version
  - Add error handling for reviewer failures
  - Persist checkpoint after reviewer completes
  - _Requirements: ORCH-REQ-003, ORCH-REQ-004_
  - _Note: Depends on reviewer component; requires Pinecone (LIVE_TESTS=1)_

- [ ] 12. Implement Send API for parallel theme-coder agents
  - Create Send tasks for theme-coder agents
  - Pass state + codebook to each theme-coder agent node
  - Collect theme proposals from all agents
  - Handle partial failures
  - _Requirements: ORCH-REQ-003, ORCH-REQ-005_
  - _Note: No LLM calls yet; use mock theme responses_

- [ ] 13. Integrate theme_aggregator_node
  - Call theme-aggregator component with theme proposals
  - Update state with final themes
  - Add error handling for aggregator failures
  - Persist checkpoint after theme aggregator completes
  - _Requirements: ORCH-REQ-003, ORCH-REQ-004_
  - _Note: Depends on theme-aggregator component_

- [ ] 14. Implement complete_node
  - Persist final results to database (analysis_jobs table)
  - Update job status to "completed"
  - Calculate and log actual cost vs estimate
  - Return final state
  - _Requirements: ORCH-REQ-001, ORCH-REQ-008_
  - _Note: Requires database; gate with LIVE_TESTS=1_

- [ ] 15. Add cost tracking metadata
  - Track token usage for each LLM call in state.metadata
  - Calculate total cost on job completion
  - Log warning if actual cost exceeds estimate by >20%
  - _Requirements: ORCH-REQ-008_
  - _Note: Integrates with cost-manager component_

- [ ] 16. Implement error recovery logic
  - Add try/except blocks around each node function
  - Log errors with analysis_id, stage, error details
  - Persist failed checkpoints with error information
  - Implement retry logic for transient errors (exponential backoff)
  - _Requirements: ORCH-REQ-005_
  - _Note: Error handling; no API calls_

- [ ] 17. Add structured logging
  - Log pipeline start with analysis_id, account_id, tenant_id
  - Log each stage completion with duration_ms
  - Log pipeline completion with total_duration_ms, codes_generated, themes_generated
  - Log failures with error_code, error_message
  - Ensure no raw interaction text at INFO level
  - _Requirements: ORCH-REQ-010_
  - _Note: Integrates with observability component_

- [ ] 18. Write integration test for full pipeline
  - Test with small dataset (5-10 interactions)
  - Verify all stages execute in sequence
  - Verify checkpoints are persisted
  - Verify final results match expected structure
  - Gate with LIVE_TESTS=1 for real LLM/DB calls
  - _Requirements: ORCH-REQ-009, All requirements_
  - _Note: E2E test; requires all components and LIVE_TESTS=1_

- [ ] 19. Write integration test for identity loading
  - Test that shared loader is called at process start
  - Verify identities are accessible to coder agents
  - Test that orchestrator surfaces loader validation errors correctly
  - Verify fail-fast behavior when shared loader raises exceptions
  - _Requirements: ORCH-REQ-006_
  - _Note: Integration test; tests error surfacing from shared loader_

- [ ] 20. Add DRY_RUN mode support
  - Check DRY_RUN environment variable
  - If DRY_RUN=1, use mock LLM responses
  - If DRY_RUN=0, use real LLM API calls
  - Test both modes
  - _Requirements: ORCH-REQ-009_
  - _Note: Testing infrastructure; no API calls in DRY_RUN mode_

## B. Phase B Part 1 — Execute Later (NEW - Simplified Coder Pipeline)

**Execute these tasks AFTER coder-agents spec is complete, BEFORE other orchestrator tasks.**

- [ ] ORCH-B1-001. Update DEPENDENCIES.yaml to consume internal/agents-coder@v1
  - Add `consumes_internal` section with internal/agents-coder@v1 interface
  - Document required fields: codes, token_usage
  - Add note: "No dependency on cost-manager in Phase B Part 1"
  - Update internal_dependencies to mark aggregator/reviewer/theme as deferred
  - _Requirements: ORCH-REQ-003_
  - _Note: Documentation only; no code changes_

- [ ] ORCH-B1-002. Update requirements.md with Phase B Part 1 overlay
  - Under Requirement 3 (Agent Coordination): Add Part 1 acceptance criteria for direct coder invocation without aggregator/reviewer/theme
  - Under Requirement 8 (Cost Tracking): Add Part 1 acceptance criteria for token-usage-only (no cost calculation)
  - Under Requirement 6 (Identity Configuration): Clarify identities loaded once at process start
  - Under Requirement 9 (Live Test Gating): Add Part 1 DRY_RUN/LIVE_TESTS behavior clarification
  - _Requirements: ORCH-REQ-003, ORCH-REQ-006, ORCH-REQ-008, ORCH-REQ-009_
  - _Note: Documentation only; no code changes_

- [ ] ORCH-B1-003. Update design.md with coder_node details
  - Add "Phase B Part 1 Architecture" section with simplified graph diagram: [fetch_data] → [coder_node] → [complete]
  - Add "Phase B Part 1: Coder Node Implementation" section with:
    * Fan-out per identity/chunk logic
    * Semaphore rate-limit (max_parallel_llm_calls) implementation example
    * Gather to state["codes"] logic
    * Token usage tracking in state["metadata"]
  - Add "Configuration Knobs (Phase B Part 1)" section documenting: DRY_RUN, LIVE_TESTS, max_parallel_llm_calls, chunk_max_tokens, IDENTITIES_PATH
  - Note what's deferred: aggregator, reviewer, theme stages, cost calculation
  - _Requirements: ORCH-REQ-003, ORCH-REQ-006, ORCH-REQ-008_
  - _Note: Documentation only; no code changes_

- [ ] ORCH-B1-004. Replace placeholder coding step with coder_node for Part 1 execution path
  - Modify StateGraph to route: fetch_data → coder_node → complete (bypass aggregator/reviewer/theme)
  - Implement coder_node function:
    * Load identities once at module init (reuse IDENTITIES from utils)
    * Chunk interactions using models/chunking@v1
    * Fan-out async calls to internal/agents-coder@v1 per identity/chunk
    * Apply semaphore rate-limit (max_parallel_llm_calls from config)
    * Gather codes into state["codes"]
    * Track token usage in state["metadata"]["token_usage"]
  - Keep other nodes (aggregator, reviewer, theme) present but off the Part 1 route
  - Write unit tests for coder_node logic (mock coder agent responses)
  - _Requirements: ORCH-REQ-003, ORCH-REQ-006, ORCH-REQ-008_
  - _Note: Core implementation; depends on internal/agents-coder@v1_

- [ ] ORCH-B1-005. Add/confirm configuration knobs used by orchestrator
  - Document in config/settings.py or steering docs:
    * DRY_RUN (default: 1)
    * LIVE_TESTS (default: 0)
    * max_parallel_llm_calls (default: 5)
    * chunk_max_tokens (default: 500)
    * IDENTITIES_PATH (default: "identities.yaml")
  - Note: No pricing fields in Part 1 (deferred to Part 2+)
  - Add validation for required config values
  - Write unit tests for config loading
  - _Requirements: ORCH-REQ-001, ORCH-REQ-009_
  - _Note: Configuration; no API calls_

## C. Phase B Part 2+ (Deferred — Do Not Execute Yet)

**These tasks implement the full pipeline with aggregator/reviewer/theme stages. Execute AFTER Phase B Part 1 is complete and validated.**

- [ ] 8. Implement fetch_data_node (DEFERRED - enhance for deep DB integration)
  - Query database for interactions in date range
  - Apply RLS (set app.current_account_id session variable)
  - Chunk interactions using models/chunking@v1 logic
  - Update state with interactions and interaction_ids
  - Write integration test (requires LIVE_TESTS=1 for real DB)
  - _Requirements: ORCH-REQ-001, ORCH-REQ-002_
  - _Note: Requires database; gate with LIVE_TESTS=1_

- [ ] 9. Implement Send API for parallel coder agents (DEFERRED - full Send API pattern)
  - Create Send tasks for each identity in identities list
  - Pass state + identity to each coder agent node
  - Collect outputs from all coder agents
  - Handle partial failures (log errors, continue with successes)
  - _Requirements: ORCH-REQ-003, ORCH-REQ-005_
  - _Note: No LLM calls yet; use mock coder responses_

- [ ] 10. Integrate code_aggregator_node (DEFERRED)
  - Call code-aggregator component with coder outputs
  - Update state with aggregated codes
  - Add error handling for aggregator failures
  - _Requirements: ORCH-REQ-003_
  - _Note: Depends on code-aggregator component_

- [ ] 11. Integrate reviewer_node (DEFERRED)
  - Call reviewer component with aggregated codes
  - Update state with codebook_version
  - Add error handling for reviewer failures
  - Persist checkpoint after reviewer completes
  - _Requirements: ORCH-REQ-003, ORCH-REQ-004_
  - _Note: Depends on reviewer component; requires Pinecone (LIVE_TESTS=1)_

- [ ] 12. Implement Send API for parallel theme-coder agents (DEFERRED)
  - Create Send tasks for theme-coder agents
  - Pass state + codebook to each theme-coder agent node
  - Collect theme proposals from all agents
  - Handle partial failures
  - _Requirements: ORCH-REQ-003, ORCH-REQ-005_
  - _Note: No LLM calls yet; use mock theme responses_

- [ ] 13. Integrate theme_aggregator_node (DEFERRED)
  - Call theme-aggregator component with theme proposals
  - Update state with final themes
  - Add error handling for aggregator failures
  - Persist checkpoint after theme aggregator completes
  - _Requirements: ORCH-REQ-003, ORCH-REQ-004_
  - _Note: Depends on theme-aggregator component_

- [ ] 14. Implement complete_node (DEFERRED - enhance with cost calculation)
  - Persist final results to database (analysis_jobs table)
  - Update job status to "completed"
  - Calculate and log actual cost vs estimate
  - Return final state
  - _Requirements: ORCH-REQ-001, ORCH-REQ-008_
  - _Note: Requires database; gate with LIVE_TESTS=1_

- [ ] 15. Add cost tracking metadata (DEFERRED - full cost calculation)
  - Track token usage for each LLM call in state.metadata
  - Calculate total cost on job completion
  - Log warning if actual cost exceeds estimate by >20%
  - _Requirements: ORCH-REQ-008_
  - _Note: Integrates with cost-manager component_

- [ ] 16. Implement error recovery logic (DEFERRED - enhance for full pipeline)
  - Add try/except blocks around each node function
  - Log errors with analysis_id, stage, error details
  - Persist failed checkpoints with error information
  - Implement retry logic for transient errors (exponential backoff)
  - _Requirements: ORCH-REQ-005_
  - _Note: Error handling; no API calls_

- [ ] 17. Add structured logging (DEFERRED - enhance for full pipeline)
  - Log pipeline start with analysis_id, account_id, tenant_id
  - Log each stage completion with duration_ms
  - Log pipeline completion with total_duration_ms, codes_generated, themes_generated
  - Log failures with error_code, error_message
  - Ensure no raw interaction text at INFO level
  - _Requirements: ORCH-REQ-010_
  - _Note: Integrates with observability component_

- [ ] 18. Write integration test for full pipeline (DEFERRED)
  - Test with small dataset (5-10 interactions)
  - Verify all stages execute in sequence
  - Verify checkpoints are persisted
  - Verify final results match expected structure
  - Gate with LIVE_TESTS=1 for real LLM/DB calls
  - _Requirements: ORCH-REQ-009, All requirements_
  - _Note: E2E test; requires all components and LIVE_TESTS=1_

- [ ] 19. Write integration test for identity loading (DEFERRED - already covered in Part 1)
  - Test that shared loader is called at process start
  - Verify identities are accessible to coder agents
  - Test that orchestrator surfaces loader errors correctly
  - Verify fail-fast behavior when shared loader raises exceptions
  - _Requirements: ORCH-REQ-006_
  - _Note: Integration test; tests error surfacing from shared loader_
