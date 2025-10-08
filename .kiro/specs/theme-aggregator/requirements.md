---
spec_id: theme-aggregator
name: Theme Aggregator
version: 1.0.0
status: draft
owners: ["@dev-team"]
provides:
  - models/themes@v1
consumes:
  - internal/agents-theme-coder@v1
  - models/quote_id@v1
---

# Requirements: Theme Aggregator

## Introduction

The theme aggregator merges and curates final themes from multiple theme coder agents. It deduplicates similar themes, consolidates supporting quotes, and applies quality thresholds to produce the final themes output.

## Requirements

### Requirement 1: Theme Merging and Deduplication

**User Story**: As a theme aggregator, I want to merge similar themes from multiple agents, so that the final output is concise and non-redundant.

#### Acceptance Criteria

1. WHEN receiving themes from multiple theme coder agents with similar titles, THE SYSTEM SHALL merge them into a single theme
2. WHEN merging themes, THE SYSTEM SHALL use semantic similarity (>0.80) to detect duplicates
3. WHEN merging themes, THE SYSTEM SHALL select the most descriptive title and description
4. WHEN themes are below similarity threshold, THE SYSTEM SHALL keep them as separate themes
5. WHEN merging completes, THE SYSTEM SHALL ensure each final theme is distinctive

### Requirement 2: Quote Consolidation

**User Story**: As a theme aggregator, I want to consolidate supporting quotes, so that each theme has the best representative evidence.

#### Acceptance Criteria

1. WHEN merging themes, THE SYSTEM SHALL combine quotes from all source themes
2. WHEN consolidating quotes, THE SYSTEM SHALL deduplicate by quote_id (exact match)
3. WHEN selecting quotes for final themes, THE SYSTEM SHALL prefer diverse quotes from different interactions
4. WHEN a theme has >10 quotes, THE SYSTEM SHALL select the 3-10 most representative quotes
5. WHEN consolidating completes, THE SYSTEM SHALL ensure all quote_ids match the canonical pattern from models/quote_id@v1

### Requirement 3: Quality Thresholds

**User Story**: As a theme aggregator, I want to apply quality thresholds, so that only robust themes are included in the final output.

#### Acceptance Criteria

1. WHEN evaluating themes, THE SYSTEM SHALL require ≥3 distinct interactions per theme (configurable via MIN_INTERACTIONS_PER_THEME)
2. WHEN a theme has <3 interactions, THE SYSTEM SHALL either merge it with a similar theme or exclude it from final output
3. WHEN evaluating theme quality, THE SYSTEM SHALL ensure themes have meaningful titles (not generic like "Theme 1")
4. WHEN evaluating theme quality, THE SYSTEM SHALL ensure themes have non-empty descriptions (min 10 characters)
5. WHEN quality validation fails, THE SYSTEM SHALL log warnings and exclude low-quality themes

### Requirement 4: Codebook Version Linking

**User Story**: As a theme aggregator, I want to link themes to their source codebook, so that results are traceable and reproducible.

#### Acceptance Criteria

1. WHEN creating final themes, THE SYSTEM SHALL include the codebook_version used for theme generation
2. WHEN linking to codebook, THE SYSTEM SHALL verify the codebook_version exists and is valid
3. WHEN themes reference code_ids, THE SYSTEM SHALL verify the code_ids exist in the referenced codebook version
4. WHEN codebook linking fails, THE SYSTEM SHALL log an error but continue with theme creation
5. WHEN final themes are created, THE SYSTEM SHALL include analysis_id, account_id, and created_at metadata

### Requirement 5: Output Structure Validation

**User Story**: As a theme aggregator, I want to validate output structure, so that themes conform to the models/themes@v1 contract.

#### Acceptance Criteria

1. WHEN producing final themes, THE SYSTEM SHALL validate the output against models/themes@v1 schema
2. WHEN validation succeeds, THE SYSTEM SHALL return the themes in the correct JSON structure
3. WHEN validation fails, THE SYSTEM SHALL log detailed errors and attempt to fix common issues
4. WHEN themes are empty (no valid themes found), THE SYSTEM SHALL return an empty themes array (valid case)
5. WHEN output is created, THE SYSTEM SHALL include all required fields: analysis_id, account_id, codebook_version, themes, created_at

### Requirement 6: Error Handling

**User Story**: As a theme aggregator, I want robust error handling, so that partial failures don't block theme generation.

#### Acceptance Criteria

1. WHEN receiving invalid theme proposals, THE SYSTEM SHALL skip malformed themes and log warnings
2. WHEN quote_id validation fails, THE SYSTEM SHALL skip invalid quotes and continue processing
3. WHEN all themes fail quality thresholds, THE SYSTEM SHALL return empty themes array with metadata
4. WHEN validation errors occur, THE SYSTEM SHALL log detailed context (theme titles, quote counts, error details)
5. WHEN any error occurs, THE SYSTEM SHALL ensure output still conforms to models/themes@v1 schema

### Requirement 7: Performance and Scalability

**User Story**: As a theme aggregator, I want efficient processing, so that theme aggregation completes quickly even with many input themes.

#### Acceptance Criteria

1. WHEN processing themes, THE SYSTEM SHALL handle up to 50 input themes efficiently (typical scale)
2. WHEN merging themes, THE SYSTEM SHALL use efficient similarity algorithms (avoid O(n²) where possible)
3. WHEN processing completes, THE SYSTEM SHALL finish within 2 seconds for typical workloads (10-20 themes)
4. WHEN memory usage exceeds reasonable limits, THE SYSTEM SHALL log warnings
5. WHEN processing large theme sets, THE SYSTEM SHALL provide progress logging
