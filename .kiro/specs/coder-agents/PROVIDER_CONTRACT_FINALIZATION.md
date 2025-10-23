# Provider Contract Finalization: Coder-Agents Spec

## Summary

This document summarizes the holistic updates made to finalize the coder-agents provider contract (internal/agents-coder@v1) and ensure documentation consistency across requirements.md, design.md, and tasks.md.

## Changes Made

### 1. Provider Interface Shape (internal/agents-coder@v1)

**Defined CoderResult TypedDict**:
```python
class TokenUsage(TypedDict):
    """Token usage tracking."""
    prompt_tokens: int
    completion_tokens: int

class CoderResult(TypedDict):
    """Result from coder agent (internal/agents-coder@v1 interface).
    
    This is the provider contract for the coder agent interface.
    """
    codes: list[Code]
    token_usage: TokenUsage
```

**Key Points**:
- CoderResult is the return type for `CoderAgent.code_chunk()`
- Token usage is part of the output object (not just logs)
- DRY_RUN mode returns mock token_usage (prompt_tokens=100, completion_tokens=50)

### 2. Requirements.md Updates

**REQ-4 (Token Usage Tracking)**:
- Changed: "return token usage in the output metadata"
- To: "return a CoderResult object containing codes and token_usage"

**REQ-7 (DRY_RUN and LIVE_TESTS)**:
- Changed: "return mock codes"
- To: "return mock CoderResult"
- Changed: "return mock token usage"
- To: "return mock token usage in CoderResult"

### 3. Design.md Updates

**Agent Types Section**:
- Added `TokenUsage` TypedDict
- Added `CoderResult` TypedDict with docstring noting it's the provider contract

**CoderAgent.code_chunk() Signature**:
- Changed return type from `List[Code]` to `CoderResult`
- Updated docstring to note it returns "CoderResult with codes and token_usage (internal/agents-coder@v1 interface)"

**CoderAgent Implementation**:
- Extract token_usage from LLM response
- Return `{"codes": codes, "token_usage": token_usage}` instead of just `codes`
- On error, return `{"codes": [], "token_usage": {"prompt_tokens": 0, "completion_tokens": 0}}`

**Mock Method**:
- Renamed `_mock_codes()` to `_mock_result()`
- Returns CoderResult with mock token_usage (prompt_tokens=100, completion_tokens=50)

**JSON Safety Wording**:
- Changed: "Three-strategy parsing"
- To: "Four strategies + dict normalization"
- Clarified: direct → ```json fenced → bare ``` fenced → regex extraction
- Added: "If result is dict with 'codes' key, normalize to list and log WARNING"

**Retry Typing**:
- Changed: `fn: Callable[..., T]`
- To: `fn: Callable[..., Awaitable[T]]`
- Added: `from typing import Awaitable` import
- This makes the callable param mypy-clean under strict mode

### 4. Tasks.md Updates

**COD-TASK-007 (Agent Types)**:
- Added TokenUsage and CoderResult to the types to implement
- Added test cases for TokenUsage and CoderResult instantiation
- Updated acceptance: "CoderResult interface validated"

**COD-TASK-009 (LLM Call)**:
- Clarified that usage dict contains both 'prompt_tokens' and 'completion_tokens'
- Updated test cases to verify both token fields
- Updated acceptance: "usage with both token fields logged"

**COD-TASK-010 (Integration)**:
- Added: "Extracts token_usage from response"
- Added: "Returns CoderResult with codes and token_usage"
- Updated test cases to verify CoderResult structure
- Added: "Verify CoderResult structure matches internal/agents-coder@v1 interface"
- Updated acceptance: "CoderResult with token_usage returned"

**COD-TASK-011 (DRY_RUN)**:
- Renamed `_mock_codes()` to `_mock_result()`
- Changed: "returns mock codes" to "returns mock CoderResult"
- Added test case: "Mock token_usage contains prompt_tokens=100 and completion_tokens=50"
- Updated acceptance: "mock CoderResult with token_usage validated"

**COD-TASK-012 (Live Test)**:
- Added: "CoderResult returned with codes and token_usage"
- Added: "CoderResult structure matches internal/agents-coder@v1 interface"
- Updated acceptance: "CoderResult validated"

## Provider Contract Summary

### internal/agents-coder@v1 Interface

**Input**:
- `chunk`: dict with text, chunk_index, start_pos, end_pos
- `interaction_id`: UUID string

**Output** (CoderResult):
```python
{
    "codes": [
        {
            "label": str,
            "quotes": [
                {
                    "quote_id": str,
                    "text": str,
                    "interaction_id": str,
                    "chunk_index": int,
                    "start_pos": int,
                    "end_pos": int
                }
            ]
        }
    ],
    "token_usage": {
        "prompt_tokens": int,
        "completion_tokens": int
    }
}
```

**Behavior**:
- Returns 0-3 codes per chunk
- Each code has 1-3 quotes
- Token usage always included (even on error: 0/0)
- DRY_RUN mode returns mock values (100/50)

## Consistency Checks

✅ **Requirements.md**: REQ-4 and REQ-7 updated to reference CoderResult
✅ **Design.md**: CoderResult defined, code_chunk returns CoderResult, JSON safety wording corrected, retry typing fixed
✅ **Tasks.md**: All tasks (007, 009, 010, 011, 012) updated to test CoderResult
✅ **Provider Contract**: Clearly documented in design.md with exact schema

## Validation

All changes maintain consistency across the three spec files:
- Requirements define WHAT (CoderResult with token_usage)
- Design defines HOW (TypedDict structure, implementation details)
- Tasks define TESTS (verify CoderResult structure in all test cases)

## Next Steps

1. Review these changes
2. Execute coder-agents tasks (COD-TASK-001 through COD-TASK-012)
3. Validate CoderResult interface with unit tests
4. Execute orchestrator Phase B Part 1 tasks (which consume this interface)
