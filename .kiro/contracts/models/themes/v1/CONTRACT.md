# Themes Model Contract v1

## Purpose

Themes represent higher-level patterns synthesized from the codebook. Each theme groups related codes and provides representative quotes that exemplify the theme.

## Theme Generation Process

### Input
- Codebook from `models/codebook@v1` (potentially compressed if > 100 codes or > 50k tokens)
- Active codes only (decay_score ≥ 0.2, unless reactivated in current analysis)
- All code labels, descriptions, and at least 1 quote per code

### Processing
1. **Theme Coder Agents**: Multiple LLM agents analyze codebook holistically
   - Identify patterns and groupings across codes
   - Generate theme titles and descriptions
   - Select representative quotes for each theme
   - May use different identity perspectives for diversity

2. **Theme Aggregator**: Consolidates outputs from theme coders
   - Merges duplicate or highly overlapping themes
   - Ensures each theme is distinctive
   - Validates quality thresholds (minimum interactions per theme)
   - Consolidates supporting quotes and code references

### Output
- Array of themes with titles, descriptions, quotes, and supporting code IDs
- Linked to specific codebook version for traceability
- Stored in database `themes` table keyed by `analysis_id`

## Quality Thresholds

### Minimum Interactions Per Theme
- Each theme must be supported by quotes from ≥ 3 distinct interactions
- Configurable via `MIN_INTERACTIONS_PER_THEME` (default: 3)
- Themes below threshold are flagged for review or merged with others
- Ensures themes represent patterns, not isolated incidents

### Theme Distinctiveness
- Themes should not significantly overlap in meaning
- Theme aggregator merges themes with high semantic similarity (> 0.80)
- Each theme should cover a unique aspect of the data

### Quote Quality
- Quotes should be representative and clear
- Avoid overly short quotes (< 20 characters)
- Prefer quotes that directly illustrate the theme
- Include diverse perspectives when available

## Quote Selection Strategy

### Representative Examples
- Select quotes that best exemplify the theme
- Prioritize clarity and specificity over length
- Include quotes from different codes supporting the theme
- Aim for 3-5 quotes per theme (configurable)

### Diversity
- Include quotes from different interactions (no duplicates from same interaction)
- Represent different facets of the theme when possible
- Balance between typical examples and edge cases

### Traceability
- All quotes must reference valid `quote_id` from codebook
- `quote_id` format defined in `models/quote_id@v1`
- Enables tracing back to original interaction text

## Codebook Version Linking

### Purpose
- Links themes to specific codebook version used for generation
- Enables reproducibility and audit trail
- Supports incremental analysis (compare themes across versions)

### Usage
- `codebook_version` field references version from `models/codebook@v1`
- Format: `v{integer}` (e.g., "v42")
- Must match existing codebook version in database

### Retrieval
- Themes can be retrieved with their source codebook for full context
- Enables understanding which codes contributed to each theme
- Supports theme evolution analysis over time

## Code IDs Reference

### Purpose
- Links themes back to supporting codes in codebook
- Enables drill-down from theme to codes to quotes
- Supports theme validation and refinement

### Format
- Array of UUIDs matching `code_id` from codebook
- Minimum 1 code per theme (typically 3-10 codes)
- Codes must exist in referenced `codebook_version`

### Validation
- All `code_ids` must be valid UUIDs
- All `code_ids` should exist in referenced codebook (soft validation)
- Warn if code not found (may indicate codebook inconsistency)

## Quote ID Format

All quotes must use the canonical quote ID format defined in `models/quote_id@v1`:
- Simple: `{interaction_id}:ch_{chunk_index}:{start_pos}-{end_pos}`
- Email threads: `{interaction_id}:msg_{message_index}:ch_{chunk_index}:{start_pos}-{end_pos}`

See `models/quote_id/v1/CONTRACT.md` for full specification.

## Validation Rules

### Theme Validation
- `title` must be non-empty and ≤ 200 characters
- `description` must be non-empty
- `quotes` array must have ≥ 3 quotes (MIN_INTERACTIONS_PER_THEME)
- `code_ids` array must have ≥ 1 code ID
- `theme_id` must be valid UUID

### Quote Validation
- `quote_id` must match canonical regex pattern
- `text` must be non-empty
- `interaction_id` must be valid UUID

### Themes Collection Validation
- `codebook_version` must match pattern `^v\d+$`
- `themes` array can be empty (no themes found, rare)
- `analysis_id` must be valid UUID
- `created_at` must be valid ISO 8601 timestamp
