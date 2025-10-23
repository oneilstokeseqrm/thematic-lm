# Phase B Part 1 — Final Holistic Revision Summary

## Overview

Completed end-to-end revision of coder-agents spec with critical updates:

1. **Quotes Array Structure** — Each code MUST have 1-3 quotes (not single quote)
2. **Option A JSON Parser** — Added bare fences + dict normalization with WARNING
3. **Regex-Based Chunking** — No str.index bugs; uses regex spans for paragraphs/sentences
4. **Enhanced Validation** — Drop codes with no valid quotes; exact offset checks
5. **Updated Prompt** — Requests quotes array format with text/start_pos/end_pos per quote

---

## Diff Summary by File

### requirements.md Changes

**REQ-2: Quote Extraction with Exact Offsets**
- ✅ Changed: "extract at least 1 representative quote" → "include a quotes array with minimum 1 and maximum 3 quotes"
- ✅ Added: "WHEN a code has no valid quotes after validation, THE SYSTEM SHALL drop the entire code"
- ✅ Clarified: 8 acceptance criteria (was 7)

**REQ-3: LLM Integration with Retry Logic**
- ✅ Changed: "request 1-3 codes per chunk" → "request 1-3 codes per chunk, each with a quotes array containing 1-3 quotes"
- ✅ Added: "WHEN calling the LLM, THE SYSTEM SHALL instruct that each quote must include text, start_pos, and end_pos fields"
- ✅ Added: "THE SYSTEM SHALL NOT log raw LLM content at INFO level"
- ✅ Clarified: 9 acceptance criteria (was 7)

**REQ-5: JSON Safety and Parsing (Option A)**
- ✅ Renamed: Added "(Option A)" to title
- ✅ Added: "WHEN direct parsing fails, THE SYSTEM SHALL also attempt to extract JSON from bare ``` fenced blocks"
- ✅ Changed: "non-greedy regex" → "non-greedy regex pattern" (clarified)
- ✅ Added: "WHEN the parsed result is a dict with 'codes' key, THE SYSTEM SHALL normalize to the list and log at WARNING level"
- ✅ Clarified: 8 acceptance criteria (was 6)

---

### design.md Changes

**utils/json_safety.py**
- ✅ Added Strategy 3: Bare ``` fenced block extraction (no language tag)
- ✅ Changed regex: `r'\[.*?\]'` → `r'\[[\s\S]*?\]'` (non-greedy with explicit whitespace/non-whitespace)
- ✅ Added: Dict normalization with WARNING log when "codes" key detected
- ✅ Updated docstring: "Option A" + 4 strategies (was 3)

**utils/chunking.py**
- ✅ Complete rewrite: Regex-based span detection (no str.index accumulation)
- ✅ Paragraph regex: `r'(.*?)(?:\n\n|$)'` with re.DOTALL
- ✅ Sentence regex: `r'[^.!?]+[.!?]\s*|[^.!?]+$'`
- ✅ Absolute offset calculation: `sent_abs_start = para_start + sent_rel_start`
- ✅ Updated docstring: "Uses regex-based span detection to avoid str.index accumulation bugs"

**agents/coder.py - CODER_PROMPT_TEMPLATE**
- ✅ Changed: "Extract a representative quote" → "Extract 1-3 representative quotes"
- ✅ Changed: "Provide start_pos and end_pos" → "For each quote, provide text, start_pos, and end_pos"
- ✅ Changed response format:
  ```json
  // OLD
  {
    "label": "...",
    "quote": "...",
    "start_pos": 0,
    "end_pos": 50
  }
  
  // NEW
  {
    "label": "...",
    "quotes": [
      {
        "text": "...",
        "start_pos": 0,
        "end_pos": 50
      }
    ]
  }
  ```

**agents/coder.py - code_chunk method**
- ✅ Changed: Process `raw_code["quotes"]` array instead of single `raw_code["quote"]`
- ✅ Added: Loop through quotes array with `[:3]` limit
- ✅ Added: `valid_quotes` list accumulation
- ✅ Added: Check `if valid_quotes:` before adding code
- ✅ Added: Log WARNING when dropping code with no valid quotes
- ✅ Changed: Build `Code` with `"quotes": valid_quotes` (list, not single quote)

---

### tasks.md Changes

**COD-TASK-002: utils/json_safety.py**
- ✅ Added: "(Option A)" to title
- ✅ Changed: "three strategies" → "four strategies"
- ✅ Added: Strategy 3 - bare ``` fenced block
- ✅ Added: Non-greedy regex pattern `r'\[[\s\S]*?\]'`
- ✅ Added: Test for dict with "codes" key (should normalize and log WARNING)
- ✅ Added: Acceptance check for "dict normalization with WARNING"

**COD-TASK-005: utils/chunking.py**
- ✅ Added: "(regex-based)" to title
- ✅ Added: Paragraph regex `r'(.*?)(?:\n\n|$)'` with re.DOTALL
- ✅ Added: Sentence regex `r'[^.!?]+[.!?]\s*|[^.!?]+$'`
- ✅ Added: "Uses regex ... to find paragraph/sentence spans"
- ✅ Added: "Slices original text using absolute offsets"
- ✅ Added: Test verification `chunk["text"] == text[start_pos:end_pos]`
- ✅ Changed: Acceptance from "offsets verified" → "regex-based spans verified"

**COD-TASK-008: coder prompt template**
- ✅ Changed: "verbatim quotes and offsets" → "each with a quotes array (1-3 quotes)"
- ✅ Added: "Each quote must have text, start_pos, and end_pos fields"
- ✅ Added: Test for "Request for quotes array (1-3 quotes per code) present"
- ✅ Changed: Acceptance from "formatting verified" → "quotes array format verified"

**COD-TASK-010: code_chunk integration**
- ✅ Added: "Processes quotes array (1-3 quotes per code)"
- ✅ Added: "Validates/repairs each quote"
- ✅ Added: "Enforces max 3 codes per chunk and max 3 quotes per code"
- ✅ Added: "Drops codes with no valid quotes and logs at WARNING"
- ✅ Added: Test for "Code with no valid quotes (should drop code and log WARNING)"
- ✅ Added: Test for "More than 3 quotes per code (should enforce limit)"
- ✅ Added: Test for "Verify chunk["text"][start:end] == quote["text"] for all quotes"
- ✅ Changed: Acceptance includes "quotes array validated; max limits enforced; exact offset checks pass"

---

### DEPENDENCIES.yaml Changes

**No changes required** — Already correct:
- ✅ No cost-manager dependency
- ✅ Consumes models/chunking@v1 and models/quote_id@v1
- ✅ Notes clarify token usage only (no cost calculation)

---

## Key Behavioral Changes

### 1. Quotes Array Structure (REQ-2, REQ-3)

**Before:**
```python
code = {
    "label": "Theme label",
    "quotes": [single_quote]  # Always exactly 1 quote
}
```

**After:**
```python
code = {
    "label": "Theme label",
    "quotes": [quote1, quote2, quote3]  # 1-3 quotes per code
}
```

**Impact:**
- Codes can now have multiple supporting quotes
- Validation must process quotes array (not single quote)
- Codes with no valid quotes are dropped entirely

---

### 2. Option A JSON Parser (REQ-5)

**Before:**
- 3 strategies: direct → ```json fenced → regex array
- No bare fence support
- No dict normalization

**After:**
- 4 strategies: direct → ```json fenced → bare ``` fenced → regex array
- Regex changed to `r'\[[\s\S]*?\]'` (non-greedy with explicit char classes)
- Dict with "codes" key normalized to list with WARNING log

**Impact:**
- More robust parsing (handles bare fences)
- Warns when LLM returns dict instead of array
- Better regex for nested arrays

---

### 3. Regex-Based Chunking (REQ-6)

**Before:**
```python
# Used str.index() with accumulation
para_start = text.index(para, current_start)
sent_pos = text.index(sent, sent_start)
```

**After:**
```python
# Uses regex spans (no accumulation bugs)
for para_match in para_pattern.finditer(text):
    para_start, para_end = para_match.span(1)
    
for sent_match in sent_pattern.finditer(para_text):
    sent_rel_start, sent_rel_end = sent_match.span()
    sent_abs_start = para_start + sent_rel_start
```

**Impact:**
- No str.index bugs with duplicate substrings
- Absolute offsets calculated correctly
- Handles edge cases (empty paragraphs, no trailing newline)

---

### 4. Enhanced Validation (REQ-2)

**Before:**
- Drop invalid quotes
- Continue with code even if quote invalid

**After:**
- Drop invalid quotes
- Drop entire code if no valid quotes remain
- Log WARNING for both cases

**Impact:**
- Codes always have at least 1 valid quote
- No "empty" codes in output
- Better error visibility

---

## Test Coverage Updates

### New Test Cases Added

**COD-TASK-002 (json_safety.py):**
- ✅ Bare ``` fenced block parsing
- ✅ Dict with "codes" key normalization + WARNING log

**COD-TASK-005 (chunking.py):**
- ✅ Exact offset verification: `chunk["text"] == text[start_pos:end_pos]`
- ✅ Regex-based span correctness

**COD-TASK-008 (prompt template):**
- ✅ Quotes array format in prompt

**COD-TASK-010 (code_chunk integration):**
- ✅ Code with no valid quotes (should drop code)
- ✅ More than 3 quotes per code (should enforce limit)
- ✅ Exact offset check: `chunk["text"][start:end] == quote["text"]`

---

## Execution Checklist

### Before Starting Tasks

- [ ] Review all 4 spec files (requirements.md, design.md, tasks.md, DEPENDENCIES.yaml)
- [ ] Confirm understanding of quotes array structure (1-3 quotes per code)
- [ ] Confirm understanding of Option A parser (4 strategies + dict normalization)
- [ ] Confirm understanding of regex-based chunking (no str.index)

### During Execution

- [ ] Execute tasks sequentially (COD-TASK-001 through COD-TASK-012)
- [ ] Run batch tests after each batch:
  - Batch 1: `pytest tests/unit/test_utils_*.py -v`
  - Batch 2: `pytest tests/unit/test_coder*.py -v`
  - Batch 3: `LIVE_TESTS=1 pytest tests/integration/test_coder_live.py -v`
- [ ] Verify exact offset checks pass: `chunk["text"][start:end] == quote["text"]`
- [ ] Verify quotes array limits enforced (1-3 per code)
- [ ] Verify dict normalization logs WARNING

### After Completion

- [ ] All 12 tasks completed
- [ ] All unit tests pass
- [ ] Live test passes (when LIVE_TESTS=1)
- [ ] No gaps/overlaps in chunk offsets
- [ ] Quotes array structure validated
- [ ] Ready for Phase B Part 2

---

## Files Modified

1. `.kiro/specs/coder-agents/requirements.md` — 3 requirements updated (REQ-2, REQ-3, REQ-5)
2. `.kiro/specs/coder-agents/design.md` — 3 modules updated (json_safety, chunking, coder)
3. `.kiro/specs/coder-agents/tasks.md` — 4 tasks updated (002, 005, 008, 010)
4. `.kiro/specs/coder-agents/DEPENDENCIES.yaml` — No changes (already correct)

---

## Next Steps

1. ✅ **Spec revision complete** — Review this summary
2. ⏭️ **Begin execution** — Start with COD-TASK-001
3. ⏭️ **Sequential execution** — Complete tasks 001-012 in order
4. ⏭️ **Stop after COD-TASK-012** — Await Phase B Part 2 instructions
