---
spec_id: theme-coder-agents
name: Theme Coder Agents
version: 1.0.0
status: draft
owners: ["@dev-team"]
provides:
  - internal/agents-theme-coder@v1
consumes:
  - models/codebook@v1
---

# Requirements: Theme Coder Agents

## Introduction

Theme coder agents generate theme proposals from codebook analysis. They include automatic compression for large codebooks using LLMLingua with fallback to truncation, while preserving all code IDs and representative quotes.

## Requirements

### Requirement 1: Compression Gate Trigger

**User Story**: As a theme coder agent, I want to compress large codebooks automatically, so that I can process them within LLM context limits.

#### Acceptance Criteria

1. WHEN receiving a codebook with >100 codes, THE SYSTEM SHALL trigger compression
2. WHEN receiving a codebook with >50k tokens, THE SYSTEM SHALL trigger compression
3. WHEN codebook has ≤100 codes AND ≤50k tokens, THE SYSTEM SHALL use the full codebook without compression
4. WHEN calculating token count, THE SYSTEM SHALL use tiktoken with cl100k_base encoding (OpenAI GPT-4 tokenizer)
5. WHEN compression is triggered, THE SYSTEM SHALL log the compression decision with original and target sizes

### Requirement 2: LLMLingua Integration

**User Story**: As a theme coder agent, I want to use LLMLingua for intelligent compression, so that I preserve the most important information.

#### Acceptance Criteria

1. WHEN compression is needed, THE SYSTEM SHALL use LLMLingua via LangChain DocumentCompressor
2. WHEN using LLMLingua, THE SYSTEM SHALL preserve all code IDs in the compressed output
3. WHEN using LLMLingua, THE SYSTEM SHALL preserve at least 1 representative quote per code
4. WHEN LLMLingua compression succeeds, THE SYSTEM SHALL use the compressed codebook for theme generation
5. WHEN LLMLingua is unavailable or fails, THE SYSTEM SHALL fall back to simple truncation

### Requirement 3: Fallback Compression Strategy

**User Story**: As a theme coder agent, I want a reliable fallback when LLMLingua fails, so that theme generation can continue.

#### Acceptance Criteria

1. WHEN LLMLingua is unavailable, THE SYSTEM SHALL use simple truncation with identical preservation rules
2. WHEN using fallback compression, THE SYSTEM SHALL preserve all code IDs
3. WHEN using fallback compression, THE SYSTEM SHALL preserve at least 1 quote per code
4. WHEN using fallback compression, THE SYSTEM SHALL truncate code descriptions to fit target token count
5. WHEN fallback compression is used, THE SYSTEM SHALL log the fallback decision for monitoring

### Requirement 4: Preservation Rules

**User Story**: As a theme coder agent, I want to preserve essential information during compression, so that theme generation quality is maintained.

#### Acceptance Criteria

1. WHEN compressing a codebook, THE SYSTEM SHALL preserve all code IDs (no codes lost)
2. WHEN compressing a codebook, THE SYSTEM SHALL preserve at least 1 representative quote per code
3. WHEN selecting quotes to preserve, THE SYSTEM SHALL prefer shorter, clearer quotes
4. WHEN compressing code descriptions, THE SYSTEM SHALL preserve key concepts and remove redundant text
5. WHEN compression completes, THE SYSTEM SHALL verify all codes have at least 1 quote

### Requirement 5: Theme Generation from Compressed Codebook

**User Story**: As a theme coder agent, I want to generate themes from compressed codebooks, so that I can identify patterns efficiently.

#### Acceptance Criteria

1. WHEN generating themes, THE SYSTEM SHALL use GPT-4o model
2. WHEN generating themes, THE SYSTEM SHALL analyze the compressed codebook holistically
3. WHEN generating themes, THE SYSTEM SHALL produce 3-8 themes with titles and descriptions
4. WHEN generating themes, THE SYSTEM SHALL select representative quotes for each theme
5. WHEN LIVE_TESTS=1, THE SYSTEM SHALL use real LLM API calls for theme generation
6. WHEN DRY_RUN=1, THE SYSTEM SHALL return mock themes without calling the LLM API

### Requirement 6: Full Codebook Preservation

**User Story**: As a system operator, I want the full codebook preserved in storage, so that no information is permanently lost.

#### Acceptance Criteria

1. WHEN compression is used, THE SYSTEM SHALL only compress the input to theme generation (not storage)
2. WHEN theme generation completes, THE SYSTEM SHALL discard the compressed version from memory
3. WHEN accessing the codebook for other purposes, THE SYSTEM SHALL use the full uncompressed version
4. WHEN compression fails, THE SYSTEM SHALL still have access to the full codebook

### Requirement 7: Cost Tracking

**User Story**: As a system operator, I want to track theme generation costs, so that I can monitor LLM usage.

#### Acceptance Criteria

1. WHEN calling the LLM for theme generation, THE SYSTEM SHALL record prompt_tokens and completion_tokens
2. WHEN theme generation completes, THE SYSTEM SHALL calculate cost (tokens × model pricing)
3. WHEN theme coder agent completes, THE SYSTEM SHALL return token usage and cost in metadata

### Requirement 8: Error Handling

**User Story**: As a theme coder agent, I want robust error handling, so that failures are graceful and recoverable.

#### Acceptance Criteria

1. WHEN LLMLingua fails, THE SYSTEM SHALL automatically fall back to truncation without manual intervention
2. WHEN LLM API calls fail, THE SYSTEM SHALL retry up to 3 times with exponential backoff
3. WHEN compression produces invalid output, THE SYSTEM SHALL log detailed errors and use fallback
4. WHEN theme generation fails after retries, THE SYSTEM SHALL return empty themes with error metadata
5. WHEN any error occurs, THE SYSTEM SHALL log sufficient context for debugging (codebook version, token counts, error details)
