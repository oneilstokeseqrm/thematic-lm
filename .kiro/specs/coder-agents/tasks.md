# Implementation Tasks: Identity-Based Coder Agents

## Task List

- [ ] 1. Create CoderAgent class structure
  - Define `__init__` with identity and LLM client parameters
  - Add `code_interaction` method signature
  - Add `_code_chunk` helper method
  - _Requirements: CODER-REQ-001_

- [ ] 2. Implement prompt template
  - Create CODER_PROMPT_TEMPLATE with JSON response format
  - Add identity prompt_prefix integration
  - Write unit tests for prompt generation
  - _Requirements: CODER-REQ-001_

- [ ] 3. Implement LLM integration
  - Configure OpenAI client with GPT-4o
  - Implement chat completion call with system + user messages
  - Add response parsing (JSON extraction)
  - Write unit tests with mock responses
  - _Requirements: CODER-REQ-003_

- [ ] 4. Implement quote ID encoding
  - Create `encode_quote_id` function per models/quote_id@v1
  - Create `find_quote_position` helper for Unicode offsets
  - Handle quote not found errors
  - Write unit tests with Unicode characters
  - _Requirements: CODER-REQ-002_

- [ ] 5. Implement chunked interaction handling
  - Process each chunk independently
  - Encode correct chunk_index in quote IDs
  - Aggregate codes from all chunks
  - Write unit tests with multi-chunk interactions
  - _Requirements: CODER-REQ-005_

- [ ] 6. Add cost tracking
  - Record prompt_tokens and completion_tokens from LLM response
  - Calculate cost using model pricing
  - Return token usage in output metadata
  - _Requirements: CODER-REQ-004_

- [ ] 7. Implement retry logic
  - Add exponential backoff for retriable errors (timeout, 5xx)
  - Max 3 retries per LLM call
  - Log retry attempts
  - _Requirements: CODER-REQ-003_

- [ ] 8. Add DRY_RUN mode support
  - Check DRY_RUN environment variable
  - Return mock codes if DRY_RUN=1
  - Use real LLM if DRY_RUN=0
  - _Requirements: CODER-REQ-006_

- [ ] 9. Write integration test with real LLM
  - Test with sample interaction
  - Verify codes and quotes generated
  - Verify quote IDs match pattern
  - Gate with LIVE_TESTS=1
  - _Requirements: CODER-REQ-006_

- [ ] 10. Write integration test for identity perspectives
  - Test with different identities (objective, empathy, critical)
  - Verify codes reflect identity perspective
  - Gate with LIVE_TESTS=1
  - _Requirements: CODER-REQ-001_
