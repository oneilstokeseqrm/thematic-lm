# Implementation Tasks: Identity-Based Coder Agents

## Batch Plan

This spec is self-contained for Phase B Part 1. Execute tasks sequentially by clicking "Start Task" in order.

**Batch 1: Utilities (COD-TASK-001 to COD-TASK-006)**
- Implement core utility modules
- Run: `pytest tests/unit/test_utils_*.py -v`

**Batch 2: Agent Implementation (COD-TASK-007 to COD-TASK-010)**
- Implement agent types and coder logic
- Run: `pytest tests/unit/test_coder*.py -v`

**Batch 3: Flags and Live Tests (COD-TASK-011 to COD-TASK-012)**
- Implement DRY_RUN mode and gated live tests
- Run: `LIVE_TESTS=1 pytest tests/integration/test_coder_live.py -v`

---

## Phase B Part 1 — Execute Now

### COD-TASK-001: Implement utils/identities.py

- [x] COD-TASK-001: Implement identity loading and validation
  - Create `src/thematic_lm/utils/identities.py`
  - Implement `Identity` dataclass with required fields (id, name, prompt_prefix) and optional field (description)
  - Implement `load_identities(path)` with @lru_cache(maxsize=1)
  - Validate required fields; fail fast on missing file or invalid schema
  - Raise ValueError if no identities defined
  - Create `tests/unit/test_utils_identities.py` with tests for:
    - Valid identities with all fields
    - Valid identities without optional description
    - Missing required fields (should raise ValueError)
    - Missing file (should raise FileNotFoundError)
    - Empty identities list (should raise ValueError)
  - **Acceptance**: All unit tests pass; cache verified with multiple calls
  - _Requirements: REQ-1_

### COD-TASK-002: Implement utils/json_safety.py

- [x] COD-TASK-002: Implement safe JSON parsing with fallback strategies (Option A)
  - Create `src/thematic_lm/utils/json_safety.py`
  - Implement `parse_json_array(content)` with four strategies:
    1. Direct JSON parse
    2. Extract from ```json fenced block (with language tag)
    3. Extract from bare ``` fenced block (no language tag)
    4. Extract first JSON array with non-greedy regex `r'\[[\s\S]*?\]'`
  - If result is dict with "codes" key, normalize to list and log WARNING
  - Return empty list on all failures; log at WARNING level (no content at INFO)
  - Create `tests/unit/test_utils_json_safety.py` with tests for:
    - Direct JSON array parsing
    - JSON with ```json fences
    - JSON with bare ``` fences
    - JSON with trailing prose
    - Dict with "codes" key (should normalize and log WARNING)
    - Malformed JSON (should return empty list and log warning)
  - **Acceptance**: All parsing strategies tested; dict normalization with WARNING; no content at INFO
  - _Requirements: REQ-5_

### COD-TASK-003: Implement utils/quotes.py

- [x] COD-TASK-003: Implement quote validation and repair
  - Create `src/thematic_lm/utils/quotes.py`
  - Implement `normalize_quote_span(quote_text, chunk_text, start_pos, end_pos)`
  - Validate offsets match quote text; attempt repair via text.index() if mismatch
  - Return None if quote not found; log at WARNING level
  - Create `tests/unit/test_utils_quotes.py` with tests for:
    - Valid offsets (should return as-is)
    - Invalid offsets but quote found (should repair and log INFO)
    - Quote not in chunk (should return None and log WARNING)
    - Unicode characters in quote and chunk
  - **Acceptance**: All validation and repair cases tested; logging verified
  - _Requirements: REQ-2_

### COD-TASK-004: Implement utils/quote_id.py

- [x] COD-TASK-004: Implement quote ID encoding and decoding
  - Create `src/thematic_lm/utils/quote_id.py`
  - Define `QUOTE_ID_PATTERN` regex per models/quote_id@v1 (supports optional msg_{n})
  - Implement `encode_quote_id(interaction_id, chunk_index, start_pos, end_pos, msg_index=None)`
  - Implement `decode_quote_id(quote_id)` that returns dict or raises ValueError
  - Create `tests/unit/test_utils_quote_id.py` with tests for:
    - Encode without msg_index
    - Encode with msg_index
    - Decode valid quote_id (round-trip test)
    - Decode invalid quote_id (should raise ValueError)
    - Unicode interaction_id (UUID format)
  - **Acceptance**: All encode/decode cases tested; regex validated
  - _Requirements: REQ-2_

### COD-TASK-005: Implement utils/chunking.py

- [x] COD-TASK-005: Implement text chunking with exact offset preservation (regex-based)
  - Create `src/thematic_lm/utils/chunking.py`
  - Define `Chunk` TypedDict per models/chunking@v1
  - Implement `chunk_text(text, max_tokens, encoding_name)` that:
    - Uses regex `r'(.*?)(?:\n\n|$)'` with re.DOTALL to find paragraph spans
    - Uses regex `r'[^.!?]+[.!?]\s*|[^.!?]+$'` to find sentence spans within long paragraphs
    - Slices original text using absolute offsets (never rejoins)
    - Returns chunks with chunk_index, text, start_pos, end_pos, token_count
  - Create `tests/unit/test_utils_chunking.py` with tests for:
    - Single paragraph (no chunking needed)
    - Multiple paragraphs (chunk by paragraph)
    - Long paragraph (chunk by sentence)
    - Unicode text (verify offsets are code-point based)
    - No gaps or overlaps in offsets (verify chunk["text"] == text[start_pos:end_pos])
  - **Acceptance**: All chunking cases tested; regex-based spans verified; no gaps/overlaps
  - _Requirements: REQ-6_

### COD-TASK-006: Implement utils/retry.py

- [x] COD-TASK-006: Implement retry logic with exponential backoff
  - Create `src/thematic_lm/utils/retry.py`
  - Implement `call_with_retry(fn, max_attempts, base_delay, timeout, *args, **kwargs)`
  - Add exponential backoff with jitter
  - Log at INFO on success after retry; WARNING on retries/timeouts
  - Create `tests/unit/test_utils_retry.py` with tests for:
    - Success on first attempt (no retry)
    - Success after 1 retry (should log INFO)
    - Timeout after max attempts (should raise last exception)
    - Exponential backoff timing (verify delays increase)
  - **Acceptance**: All retry scenarios tested; logging verified; jitter applied
  - _Requirements: REQ-3_

### COD-TASK-007: Implement agents/types.py

- [x] COD-TASK-007: Define Quote, Code, TokenUsage, and CoderResult TypedDicts
  - Create `src/thematic_lm/agents/types.py`
  - Define `Quote` TypedDict with fields: quote_id, text, interaction_id, chunk_index, start_pos, end_pos
  - Define `Code` TypedDict with fields: label, quotes (list of Quote)
  - Define `TokenUsage` TypedDict with fields: prompt_tokens, completion_tokens
  - Define `CoderResult` TypedDict with fields: codes (list of Code), token_usage (TokenUsage)
  - Create `tests/unit/test_agents_types.py` with minimal type checks:
    - Instantiate Quote with all fields
    - Instantiate Code with quotes list
    - Instantiate TokenUsage with token counts
    - Instantiate CoderResult with codes and token_usage
    - Verify TypedDict structure (no runtime validation needed)
  - **Acceptance**: Types defined; CoderResult interface validated; basic instantiation tested
  - _Requirements: REQ-2, REQ-4_

### COD-TASK-008: Implement coder prompt template

- [x] COD-TASK-008: Create coder prompt template and formatting
  - Create `src/thematic_lm/agents/coder.py` (initial structure)
  - Define `CODER_PROMPT_TEMPLATE` with JSON-array-only instruction
  - Request 1-3 codes per chunk, each with a quotes array (1-3 quotes)
  - Each quote must have text, start_pos, and end_pos fields
  - Implement `CoderAgent._build_prompt(chunk_text)` method
  - Create `tests/unit/test_coder_prompt.py` with tests for:
    - Prompt formatting with sample chunk text
    - JSON-array-only instruction present
    - Request for 1-3 codes present
    - Request for quotes array (1-3 quotes per code) present
    - Verbatim quote instruction present
  - **Acceptance**: Prompt template tested; quotes array format verified
  - _Requirements: REQ-3_

### COD-TASK-009: Implement CoderAgent._call_llm with retry

- [x] COD-TASK-009: Implement LLM call with retry and usage logging
  - In `src/thematic_lm/agents/coder.py`:
    - Implement `CoderAgent.__init__(identity, model, dry_run)`
    - Implement `CoderAgent._call_llm(messages)` that:
      - Uses `call_with_retry` from utils/retry.py
      - Returns dict with 'content' and 'usage' keys
      - Usage dict contains 'prompt_tokens' and 'completion_tokens'
      - Logs token usage (prompt_tokens, completion_tokens) at INFO level (no content)
  - Create `tests/unit/test_coder_llm.py` with mocked tests for:
    - Successful LLM call (mock response with usage containing prompt_tokens and completion_tokens)
    - LLM call with retry (mock transient failure then success)
    - LLM call timeout (mock timeout, verify WARNING log)
    - Token usage extraction from response metadata (verify both prompt_tokens and completion_tokens)
  - **Acceptance**: LLM call logic tested with mocks; retry verified; usage with both token fields logged
  - _Requirements: REQ-3, REQ-4_

### COD-TASK-010: Implement CoderAgent.code_chunk integration

- [x] COD-TASK-010: Integrate code_chunk with JSON parsing, quote validation, and quote_id encoding
  - In `src/thematic_lm/agents/coder.py`:
    - Implement `CoderAgent.code_chunk(chunk, interaction_id)` that:
      - Calls `_call_llm` with identity prompt and chunk text
      - Extracts token_usage from response (prompt_tokens, completion_tokens)
      - Parses response with `parse_json_array`
      - Processes quotes array (1-3 quotes per code)
      - Validates/repairs each quote with `normalize_quote_span`
      - Encodes quote_ids with `encode_quote_id`
      - Enforces max 3 codes per chunk and max 3 quotes per code
      - Drops invalid quotes and logs at WARNING
      - Drops codes with no valid quotes and logs at WARNING
      - Returns CoderResult with codes and token_usage
  - Create `tests/unit/test_coder_integration.py` with tests for:
    - Valid LLM response with quotes array (all quotes valid, verify CoderResult includes token_usage)
    - Invalid quote offsets (should repair)
    - Quote not found (should drop quote and log WARNING)
    - Code with no valid quotes (should drop code and log WARNING)
    - More than 3 codes (should enforce limit)
    - More than 3 quotes per code (should enforce limit)
    - Malformed JSON (should return CoderResult with empty codes list and token_usage)
    - Verify chunk["text"][start:end] == quote["text"] for all quotes
    - Verify CoderResult structure matches internal/agents-coder@v1 interface
  - **Acceptance**: Full integration tested; CoderResult with token_usage returned; quotes array validated; max limits enforced; exact offset checks pass
  - _Requirements: REQ-2, REQ-3, REQ-4, REQ-5_

### COD-TASK-011: Implement DRY_RUN mode

- [x] COD-TASK-011: Add DRY_RUN mode and test gating scaffolding
  - In `src/thematic_lm/agents/coder.py`:
    - Check `DRY_RUN` env var in `__init__` (or constructor param)
    - Implement `CoderAgent._mock_result(chunk, interaction_id)` that returns mock CoderResult
    - In `code_chunk`, return mock CoderResult if `self.dry_run` is True
    - Mock CoderResult should include valid quote_id and mock token_usage (prompt_tokens=100, completion_tokens=50)
  - Create `tests/unit/test_coder_dry_run.py` with tests for:
    - DRY_RUN=1 returns mock CoderResult (no LLM call)
    - DRY_RUN=0 calls real LLM (mocked in test)
    - Mock CoderResult has valid structure with codes and token_usage
    - Mock token_usage contains prompt_tokens=100 and completion_tokens=50
    - Mock codes have valid quote_id
  - Add `tests/conftest.py` with LIVE_TESTS gating fixture:
    - `pytest.mark.skipif(os.getenv("LIVE_TESTS") != "1", reason="Live tests disabled")`
  - **Acceptance**: DRY_RUN mode tested; mock CoderResult with token_usage validated; LIVE_TESTS gating ready
  - _Requirements: REQ-7_

### COD-TASK-012: Optional live integration test

- [x] COD-TASK-012: Create gated live integration test with real API
  - Create `tests/integration/test_coder_live.py`
  - Mark test with `@pytest.mark.skipif(os.getenv("LIVE_TESTS") != "1", ...)`
  - Test with tiny sample interaction (1-2 sentences)
  - Verify:
    - CoderResult returned with codes and token_usage
    - Codes generated (1-3 codes)
    - Quote IDs match regex pattern
    - Offsets are valid (start < end, within chunk bounds)
    - Token usage recorded (prompt_tokens > 0, completion_tokens > 0)
    - CoderResult structure matches internal/agents-coder@v1 interface
  - **Acceptance**: Live test passes when LIVE_TESTS=1; CoderResult validated; skipped otherwise
  - _Requirements: REQ-7_

---

## Phase B Part 2+ — Deferred (Do NOT Execute Yet)

**IMPORTANT**: Do not click "Start Task" on any items below until Phase B Part 2 is explicitly enabled.

### (DEFERRED) Multi-chunk orchestration test

- [ ] (DEFERRED) Test coder agent with multi-chunk interaction
  - Test with interaction requiring 3+ chunks
  - Verify chunk_index increments correctly
  - Verify quote_ids include correct chunk_index
  - Verify codes from all chunks aggregated
  - _Requirements: REQ-6_

### (DEFERRED) Identity perspective validation test

- [ ] (DEFERRED) Test different identity perspectives produce different codes
  - Test with "objective-analyst", "empathy-focused", "critical-thinker" identities
  - Verify codes reflect identity perspective (manual review)
  - Test with identities both with and without description field
  - Gate with LIVE_TESTS=1
  - _Requirements: REQ-1_

### (DEFERRED) Unicode edge cases test

- [ ] (DEFERRED) Test with complex Unicode text (emoji, CJK, RTL)
  - Verify offsets are code-point based (not byte-based)
  - Verify quote extraction works with multi-byte characters
  - Verify chunking preserves Unicode boundaries
  - _Requirements: REQ-2, REQ-6_

### (DEFERRED) Error recovery test

- [ ] (DEFERRED) Test error recovery scenarios
  - LLM returns invalid JSON (should return empty list)
  - LLM returns no quotes (should skip code)
  - LLM returns malformed offsets (should repair or drop)
  - All retries fail (should log WARNING and return empty list)
  - _Requirements: REQ-3, REQ-5_

### (DEFERRED) Performance test

- [ ] (DEFERRED) Test performance with large interaction
  - Test with 10+ chunks (5000+ tokens)
  - Verify chunking completes in <1s
  - Verify no memory leaks with large text
  - _Requirements: REQ-6_
