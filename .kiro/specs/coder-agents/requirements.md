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

Coder agents analyze interactions and generate descriptive codes with supporting quotes. Multiple agents with different identity perspectives run in parallel to capture diverse interpretations.

## Requirements

### Requirement 1: Identity-Based Coding

**User Story**: As a coder agent, I want to apply my identity perspective, so that I generate codes aligned with my analytical lens.

#### Acceptance Criteria

1. WHEN a coder agent receives an interaction and identity configuration, THE SYSTEM SHALL incorporate the identity's prompt_prefix into the LLM system prompt
2. WHEN generating codes, THE SYSTEM SHALL produce 1-3 codes per interaction as specified in the identity's instructions
3. WHEN the identity is "objective-analyst", THE SYSTEM SHALL focus on factual, observable patterns
4. WHEN the identity is "empathy-focused", THE SYSTEM SHALL focus on emotional and experiential themes
5. WHEN the identity is "critical-thinker", THE SYSTEM SHALL focus on power dynamics and systemic issues

### Requirement 2: Quote Extraction

**User Story**: As a coder agent, I want to extract representative quotes for each code, so that codes are grounded in the data.

#### Acceptance Criteria

1. WHEN generating a code, THE SYSTEM SHALL extract at least 1 representative quote from the interaction text
2. WHEN extracting a quote, THE SYSTEM SHALL encode the quote_id using the format from models/quote_id@v1
3. WHEN the interaction is chunked, THE SYSTEM SHALL include the chunk_index in the quote_id
4. WHEN extracting a quote, THE SYSTEM SHALL record start_pos and end_pos as Unicode code-point offsets
5. WHEN a quote spans multiple chunks, THE SYSTEM SHALL select the most representative single chunk

### Requirement 3: LLM Integration

**User Story**: As a coder agent, I want to call the LLM API efficiently, so that I generate high-quality codes within budget.

#### Acceptance Criteria

1. WHEN calling the LLM, THE SYSTEM SHALL use GPT-4o model
2. WHEN calling the LLM, THE SYSTEM SHALL include the identity prompt_prefix in the system message
3. WHEN calling the LLM, THE SYSTEM SHALL include the interaction text in the user message
4. WHEN the LLM call succeeds, THE SYSTEM SHALL parse the response into structured code objects
5. WHEN the LLM call fails with a retriable error, THE SYSTEM SHALL retry up to 3 times with exponential backoff

### Requirement 4: Cost Tracking

**User Story**: As a system operator, I want to track token usage per coder agent, so that I can monitor costs.

#### Acceptance Criteria

1. WHEN an LLM call completes, THE SYSTEM SHALL record prompt_tokens and completion_tokens
2. WHEN an LLM call completes, THE SYSTEM SHALL calculate cost (tokens × model pricing)
3. WHEN a coder agent completes, THE SYSTEM SHALL return token usage in the output metadata

### Requirement 5: Chunked Interaction Handling

**User Story**: As a coder agent, I want to process chunked interactions correctly, so that long texts are handled properly.

#### Acceptance Criteria

1. WHEN an interaction has multiple chunks, THE SYSTEM SHALL process each chunk independently
2. WHEN processing a chunk, THE SYSTEM SHALL generate codes specific to that chunk's content
3. WHEN encoding quote_ids, THE SYSTEM SHALL use the correct chunk_index for each quote
4. WHEN all chunks are processed, THE SYSTEM SHALL return codes from all chunks

### Requirement 6: Live Test Gating

**User Story**: As a developer, I want tests to respect LIVE_TESTS flag, so that I can test without API costs.

#### Acceptance Criteria

1. WHEN LIVE_TESTS=0, THE SYSTEM SHALL use mock LLM responses
2. WHEN LIVE_TESTS=1, THE SYSTEM SHALL use real LLM API calls
3. WHEN DRY_RUN=1, THE SYSTEM SHALL return mock codes without calling the LLM API
