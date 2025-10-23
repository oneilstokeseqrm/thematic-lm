# Phase B Part 1 — Spec Revision Summary

## Overview

Revised the coder-agents spec holistically for Phase B Part 1 with the following key changes:

1. **Removed all cost management dependencies** — Only track token usage (prompt_tokens, completion_tokens)
2. **Added concrete utility modules** — Detailed design for identities, json_safety, quotes, quote_id, chunking, retry
3. **Clarified exact offset preservation** — All chunking done by slicing original text (never rejoining)
4. **Structured tasks into executable batches** — 12 tasks (COD-TASK-001 to COD-TASK-012) with clear acceptance criteria
5. **Deferred non-essential tasks** — Moved broader integration tests to Phase B Part 2+

---

## Diff Summary

### requirements.md Changes

**Added Requirements:**
- **REQ-1**: Identity Loading and Validation (expanded from original REQ-1)
  - Load from identities.yaml at project root
  - Validate required fields (id, name, prompt_prefix)
  - Accept optional description field
  - Fail fast on missing/invalid file
  - Cache with @lru_cache(maxsize=1)

- **REQ-5**: JSON Safety and Parsing (NEW)
  - Three-strategy parsing: direct → fenced block → regex
  - Return empty list on failure (no crash)
  - Log at WARNING level (no content at INFO)

**Modified Requirements:**
- **REQ-2**: Quote Extraction with Exact Offsets (expanded)
  - Added quote repair logic (attempt to locate quote if offsets don't match)
  - Added quote_id encoding per models/quote_id@v1 (supports optional msg_{n})
  - Drop invalid quotes and log at WARNING

- **REQ-3**: LLM Integration with Retry Logic (expanded)
  - Added JSON-array-only response instruction
  - Added 1-3 codes per chunk constraint
  - Added retry logging (INFO on success after retry, WARNING on timeout)

- **REQ-4**: Token Usage Tracking (RENAMED from "Cost Tracking")
  - **REMOVED**: Cost calculation (tokens × pricing)
  - **KEPT**: Token usage tracking (prompt_tokens, completion_tokens)
  - No pricing logic in this phase

- **REQ-6**: Chunked Interaction Handling with Exact Offsets (expanded)
  - Added chunking strategy (paragraphs → sentences)
  - Added exact offset preservation rule (slice original text, never rejoin)
  - Added chunk structure (chunk_index, start_pos, end_pos, token_count)

- **REQ-7**: DRY_RUN and LIVE_TESTS Gating (expanded from REQ-6)
  - Clarified DRY_RUN=1 behavior (mock codes, no API)
  - Clarified LIVE_TESTS=1 behavior (real API in tests)
  - Added mock token usage for DRY_RUN mode

---

### design.md Changes

**Added Modules:**

1. **src/thematic_lm/utils/identities.py**
   - `Identity` dataclass (id, name, prompt_prefix, description?)
   - `load_identities(path)` with @lru_cache and validation
   - Fail fast on missing required fields or empty list

2. **src/thematic_lm/utils/json_safety.py**
   - `parse_json_array(content)` with three strategies
   - Returns empty list on failure (no crash)
   - Logs at WARNING level (no content at INFO)

3. **src/thematic_lm/utils/quotes.py**
   - `normalize_quote_span(quote_text, chunk_text, start_pos, end_pos)`
   - Validates offsets; attempts repair via text.index()
   - Returns None if quote not found; logs at WARNING

4. **src/thematic_lm/utils/quote_id.py**
   - `QUOTE_ID_PATTERN` regex per models/quote_id@v1
   - `encode_quote_id(...)` with optional msg_index
   - `decode_quote_id(...)` that raises ValueError on invalid format

5. **src/thematic_lm/utils/chunking.py**
   - `Chunk` TypedDict (chunk_index, text, start_pos, end_pos, token_count)
   - `chunk_text(text, max_tokens, encoding_name)` that slices original text
   - Splits by paragraphs → sentences; preserves exact offsets

6. **src/thematic_lm/utils/retry.py**
   - `call_with_retry(fn, max_attempts, base_delay, timeout, *args, **kwargs)`
   - Exponential backoff with jitter
   - Logs at INFO on success after retry; WARNING on timeout

7. **src/thematic_lm/agents/types.py**
   - `Quote` TypedDict (quote_id, text, interaction_id, chunk_index, start_pos, end_pos)
   - `Code` TypedDict (label, quotes)

**Modified Modules:**

8. **src/thematic_lm/agents/coder.py**
   - `CoderAgent.__init__(identity, model, dry_run)`
   - `_build_prompt(chunk_text)` — JSON-array-only instruction
   - `_call_llm(messages)` — async with retry; returns dict with 'content' and 'usage'
   - `code_chunk(chunk, interaction_id)` — full integration:
     - Parse JSON safely
     - Validate/repair quotes
     - Encode quote_ids
     - Enforce max 3 codes
     - Drop invalid quotes and log at WARNING
   - `_mock_codes(chunk, interaction_id)` — DRY_RUN mode

**Design Decisions:**
- **No cost calculation** in Phase B Part 1 (only token usage tracking)
- **Exact offset preservation** via slicing (never rejoining text)
- **JSON safety** with three-strategy parsing
- **DRY_RUN and LIVE_TESTS** respected throughout
- **Retry strategy** with exponential backoff and jitter

---

### DEPENDENCIES.yaml Changes

**Removed:**
- `internal_dependencies.cost-manager` — No cost management in Phase B Part 1

**Modified:**
- Added `notes` section clarifying:
  - No cost calculation in this phase
  - Token usage tracking only
  - Self-contained implementation
  - DRY_RUN and LIVE_TESTS flags respected

**Kept:**
- `consumes.models/chunking@v1` — Text chunking strategy
- `consumes.models/quote_id@v1` — Quote ID encoding format
- `external_dependencies.openai_api` — GPT-4o for code generation

---

### tasks.md Changes

**Structure:**
- **Batch Plan** added at top (3 batches: utilities, agent, flags/live)
- **Phase B Part 1 — Execute Now** (12 tasks: COD-TASK-001 to COD-TASK-012)
- **Phase B Part 2+ — Deferred** (5 tasks marked as DEFERRED)

**Task List (Phase B Part 1):**

| Task ID | Description | Batch | Requirements |
|---------|-------------|-------|--------------|
| COD-TASK-001 | Implement utils/identities.py + unit tests | 1 | REQ-1 |
| COD-TASK-002 | Implement utils/json_safety.py + unit tests | 1 | REQ-5 |
| COD-TASK-003 | Implement utils/quotes.py + unit tests | 1 | REQ-2 |
| COD-TASK-004 | Implement utils/quote_id.py + unit tests (regex + round-trip + unicode) | 1 | REQ-2 |
| COD-TASK-005 | Implement utils/chunking.py (slice-based) + unit tests (no gaps/overlaps, unicode) | 1 | REQ-6 |
| COD-TASK-006 | Implement utils/retry.py + unit tests (retry/timeout) | 1 | REQ-3 |
| COD-TASK-007 | Add agents/types.py (Quote/Code) + minimal type checks | 2 | REQ-2 |
| COD-TASK-008 | Coder prompt template + unit tests (formatting, JSON-array-only) | 2 | REQ-3 |
| COD-TASK-009 | CoderAgent._call_llm with retry + usage logging (tokens only) + mocked tests | 2 | REQ-3, REQ-4 |
| COD-TASK-010 | CoderAgent.code_chunk integration: safe JSON parse, quote validation/repair, quote_id attach, enforce ≤3 codes; unit tests | 2 | REQ-2, REQ-3, REQ-5 |
| COD-TASK-011 | DRY_RUN path + unit tests; LIVE_TESTS gating scaffolding in tests | 3 | REQ-7 |
| COD-TASK-012 | Optional live integration test (gated by LIVE_TESTS=1) using a tiny sample; verify structure, quote_id regex, offsets | 3 | REQ-7 |

**Deferred Tasks (Phase B Part 2+):**
- Multi-chunk orchestration test
- Identity perspective validation test
- Unicode edge cases test
- Error recovery test
- Performance test

**Key Changes:**
- All tasks are self-contained (no cross-spec dependencies)
- Each task has clear acceptance criteria
- Test commands provided for each batch
- Deferred tasks clearly marked with (DEFERRED) prefix

---

## Execution Instructions

1. **Read the spec files** (requirements.md, design.md, DEPENDENCIES.yaml, tasks.md)
2. **Execute tasks sequentially** by clicking "Start Task" in tasks.md
3. **Run tests after each batch**:
   - Batch 1: `pytest tests/unit/test_utils_*.py -v`
   - Batch 2: `pytest tests/unit/test_coder*.py -v`
   - Batch 3: `LIVE_TESTS=1 pytest tests/integration/test_coder_live.py -v`
4. **Do NOT execute deferred tasks** until Phase B Part 2 is explicitly enabled

---

## Key Constraints Enforced

✅ **No cost management** — Only token usage tracking (prompt_tokens, completion_tokens)  
✅ **Exact offset preservation** — All chunking done by slicing original text (never rejoining)  
✅ **JSON safety** — Three-strategy parsing with fallback; no crashes on malformed JSON  
✅ **Quote validation** — Attempt repair via text search; drop if invalid  
✅ **Quote ID encoding** — Per models/quote_id@v1 with optional msg_{n}  
✅ **DRY_RUN and LIVE_TESTS** — Respected throughout implementation and tests  
✅ **Self-contained** — No dependencies on orchestrator or other specs  
✅ **Sequential execution** — Tasks designed to be executed one at a time  

---

## Files Modified

1. `.kiro/specs/coder-agents/requirements.md` — 7 requirements (1 renamed, 1 new, 5 expanded)
2. `.kiro/specs/coder-agents/design.md` — 8 modules (7 new utilities, 1 modified agent)
3. `.kiro/specs/coder-agents/DEPENDENCIES.yaml` — Removed cost-manager dependency
4. `.kiro/specs/coder-agents/tasks.md` — 12 executable tasks + 5 deferred tasks

---

## Next Steps

**After spec review:**
1. Confirm spec changes are acceptable
2. Begin executing COD-TASK-001 (Implement utils/identities.py)
3. Execute tasks sequentially through COD-TASK-012
4. Stop after COD-TASK-012 and await Phase B Part 2 instructions
