# Implementation Tasks: LangGraph Pipeline Orchestrator

## Task List

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

- [ ] 3. Implement identities configuration loader
  - Create `Identity` dataclass with id, name, description, prompt_prefix
  - Implement `load_identities(path: str)` function with validation
  - Add error handling for missing/invalid YAML
  - Write unit tests with valid and invalid YAML fixtures
  - _Requirements: ORCH-REQ-006_
  - _Note: No API calls; file I/O only_

- [ ] 4. Create identities.yaml stub file
  - Generate `identities.yaml` with 2-3 example identities
  - Include: objective-analyst, empathy-focused, critical-thinker
  - Document format and required fields in comments
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
  - Test that identities.yaml is loaded at process start
  - Verify identities are accessible to coder agents
  - Test with valid and invalid YAML files
  - Verify fail-fast behavior on invalid config
  - _Requirements: ORCH-REQ-006_
  - _Note: Integration test; no API calls_

- [ ] 20. Add DRY_RUN mode support
  - Check DRY_RUN environment variable
  - If DRY_RUN=1, use mock LLM responses
  - If DRY_RUN=0, use real LLM API calls
  - Test both modes
  - _Requirements: ORCH-REQ-009_
  - _Note: Testing infrastructure; no API calls in DRY_RUN mode_
