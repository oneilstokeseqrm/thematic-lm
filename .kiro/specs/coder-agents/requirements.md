---
spec_id: coder-agents
name: Identity-Based Coder Agents
version: 1.0.0
status: Draft
owners: ["@dev-team"]
provides:
  - internal/agents-coder@v1
consumes:
  - models/chunking@v1
  - models/quote_id@v1
---

# Requirements: Identity-Based Coder Agents

## Introduction

Coder agents analyze interactions and generate descriptive codes with supporting quotes. Multiple agents with different identity perspectives run in parallel to capture diverse interpretations. This spec is self-contained for Phase B Part 1 and does not depend on cost management or orchestrator components.

## Requirements

### Requirement 1: Identity Loading and Validation

**User Story**: As a coder agent, I want to load identity configurations from identities.yaml, so that I can apply the correct analytical perspective.

#### Acceptance Criteria

1. WHEN the system starts, THE SYSTEM SHALL load identities from identities.yaml at the project root
2. WHEN loading identities, THE SYSTEM SHALL validate that each identity has required fields: id, name, prompt_prefix
3. WHEN an identity includes an optional description field, THE SYSTEM SHALL accept it without requiring it
4. WHEN identities.yaml is missing or invalid, THE SYSTEM SHALL fail fast with a clear error message
5. WHEN identities.yaml contains no identities, THE SYSTEM SHALL fail fast with a clear error message
6. WHEN identities are loaded successfully, THE SYSTEM SHALL cache them using @lru_cache(maxsize=1)

### Requirement 2: Quote Extraction with Exact Offsets

**User Story**: As a coder agent, I want to extract representative quotes with exact Unicode offsets, so that codes are precisely grounded in the data.

#### Acceptance Criteria

1. WHEN generating a code, THE SYSTEM SHALL include a quotes array with minimum 1 and maximum 3 quotes
2. WHEN extracting a quote, THE SYSTEM SHALL ensure the quote text is verbatim from the chunk
3. WHEN extracting a quote, THE SYSTEM SHALL record start_pos and end_pos as Unicode code-point offsets
4. WHEN the LLM provides offsets that don't match the quote text, THE SYSTEM SHALL attempt to repair by locating the quote text in the chunk
5. WHEN a quote cannot be validated or repaired, THE SYSTEM SHALL drop the quote and log at WARNING level
6. WHEN a code has no valid quotes after validation, THE SYSTEM SHALL drop the entire code
7. WHEN extracting a quote, THE SYSTEM SHALL encode the quote_id using the format from models/quote_id@v1 (supporting optional msg_{n})
8. WHEN the interaction is chunked, THE SYSTEM SHALL include the chunk_index in the quote_id

### Requirement 3: LLM Integration with Retry Logic

**User Story**: As a coder agent, I want to call the LLM API with retry logic, so that transient failures don't cause job failures.

#### Acceptance Criteria

1. WHEN calling the LLM, THE SYSTEM SHALL use GPT-4o model
2. WHEN calling the LLM, THE SYSTEM SHALL include the identity prompt_prefix in the system message
3. WHEN calling the LLM, THE SYSTEM SHALL include the chunk text in the user message with JSON-array-only response instructions
4. WHEN calling the LLM, THE SYSTEM SHALL request 1-3 codes per chunk, each with a quotes array containing 1-3 quotes
5. WHEN calling the LLM, THE SYSTEM SHALL instruct that each quote must include text, start_pos, and end_pos fields
6. WHEN the LLM call fails with a transient error (timeout, 5xx), THE SYSTEM SHALL retry up to 3 times with exponential backoff
7. WHEN the LLM call succeeds after retry, THE SYSTEM SHALL log at INFO level
8. WHEN the LLM call times out or fails after retries, THE SYSTEM SHALL log at WARNING level and return empty list
9. THE SYSTEM SHALL NOT log raw LLM content at INFO level

### Requirement 4: Token Usage Tracking (No Cost Calculation)

**User Story**: As a system operator, I want to track token usage per coder agent, so that I can monitor resource consumption.

#### Acceptance Criteria

1. WHEN an LLM call completes, THE SYSTEM SHALL record prompt_tokens from provider metadata
2. WHEN an LLM call completes, THE SYSTEM SHALL record completion_tokens from provider metadata
3. WHEN a coder agent completes, THE SYSTEM SHALL return a CoderResult object containing codes and token_usage (prompt_tokens, completion_tokens)
4. WHEN token usage is unavailable, THE SYSTEM SHALL log at WARNING level and continue
5. THE SYSTEM SHALL NOT calculate cost or pricing in this phase

### Requirement 5: JSON Safety and Parsing (Option A)

**User Story**: As a coder agent, I want to safely parse LLM JSON output, so that malformed responses don't crash the system.

#### Acceptance Criteria

1. WHEN parsing LLM output, THE SYSTEM SHALL attempt direct JSON parsing first
2. WHEN direct parsing fails, THE SYSTEM SHALL attempt to extract JSON from ```json fenced blocks (with or without language tag)
3. WHEN direct parsing fails, THE SYSTEM SHALL also attempt to extract JSON from bare ``` fenced blocks
4. WHEN fenced block extraction fails, THE SYSTEM SHALL attempt to extract the first JSON array using non-greedy regex pattern
5. WHEN the parsed result is a dict with "codes" key, THE SYSTEM SHALL normalize to the list and log at WARNING level
6. WHEN all parsing strategies fail, THE SYSTEM SHALL return an empty list and log at WARNING level
7. WHEN parsing succeeds, THE SYSTEM SHALL validate that the result is a list of code objects
8. THE SYSTEM SHALL NOT log raw LLM content at INFO level

### Requirement 6: Chunked Interaction Handling with Exact Offsets

**User Story**: As a coder agent, I want to process chunked interactions with exact offset preservation, so that long texts are handled correctly.

#### Acceptance Criteria

1. WHEN an interaction is long, THE SYSTEM SHALL chunk it by paragraphs then sentences using models/chunking@v1 strategy
2. WHEN chunking text, THE SYSTEM SHALL preserve exact offsets by slicing the original text (never rejoining)
3. WHEN creating a chunk, THE SYSTEM SHALL include chunk_index, start_pos, end_pos, token_count
4. WHEN processing a chunk, THE SYSTEM SHALL generate 1-3 codes specific to that chunk's content
5. WHEN encoding quote_ids, THE SYSTEM SHALL use the correct chunk_index for each quote
6. WHEN all chunks are processed, THE SYSTEM SHALL return codes from all chunks

### Requirement 7: DRY_RUN and LIVE_TESTS Gating

**User Story**: As a developer, I want tests to respect DRY_RUN and LIVE_TESTS flags, so that I can test without API costs.

#### Acceptance Criteria

1. WHEN DRY_RUN=1, THE SYSTEM SHALL return mock CoderResult without calling the LLM API
2. WHEN DRY_RUN=0 and LIVE_TESTS=0, THE SYSTEM SHALL use mock LLM responses in tests
3. WHEN DRY_RUN=0 and LIVE_TESTS=1, THE SYSTEM SHALL use real LLM API calls in tests
4. WHEN DRY_RUN=1, THE SYSTEM SHALL still validate input structure and quote_id encoding
5. WHEN DRY_RUN=1, THE SYSTEM SHALL return mock token usage (prompt_tokens=100, completion_tokens=50) in CoderResult
