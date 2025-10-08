# Codebook Model Contract v1

## Purpose

The codebook is a living repository of codes that evolves with each analysis. It maintains a structured collection of codes with supporting quotes, enabling incremental analysis and theme generation.

## Codebook Versioning Rules

### Version Snapshots
- Each analysis run creates a new codebook version (e.g., v1, v2, v3...)
- Versions are immutable once created (snapshot model)
- New analysis loads latest version as starting point
- Version identifier format: `v{integer}` (e.g., "v42")

### Version Creation Triggers
- After each coding stage completion (reviewer agent updates)
- Before theme generation stage (ensures consistent input)
- On manual codebook reset (rare, requires admin action)

### Version Storage
- Full codebook stored in database `codebook_versions` table
- Keyed by `account_id` and `version`
- Includes all codes, quotes, and metadata
- Retention: Indefinite (all versions preserved for audit trail)

## Code Merging Strategy

### Similarity Threshold
- Codes are merged if cosine similarity > 0.85 (configurable)
- Similarity computed on code embeddings (text-embedding-3-large)
- Reviewer agent performs top-k similarity search (k=5) for each new code

### Merge Logic
- If similar code exists (similarity > threshold):
  - Keep existing `code_id` (stability)
  - Update `label` if new label is more descriptive (LLM decides)
  - Append new quotes to existing code's quotes array
  - Update `updated_at` timestamp
  - Increment usage counter (affects decay_score)
- If no similar code exists:
  - Generate new `code_id` (UUID)
  - Add code to codebook with initial quotes
  - Set `decay_score` = 1.0 (fully active)

### Merge Conflicts
- If multiple new codes match same existing code:
  - Merge all into existing code
  - Combine quotes from all sources
  - Deduplicate quotes by `quote_id`

## Decay Scoring Mechanism

### Purpose
Track code usage over time to identify inactive codes that should be filtered from theme generation.

### Scoring Algorithm
```
decay_score = base_score * time_decay_factor * usage_factor

where:
- base_score = 1.0 for new codes
- time_decay_factor = exp(-λ * days_since_last_update), λ = 0.01 (configurable)
- usage_factor = min(1.0, quote_count / 10)  # Saturates at 10 quotes
```

### Score Interpretation
- **1.0**: Highly active (recently used, many quotes)
- **0.5-0.9**: Moderately active
- **0.2-0.5**: Low activity (consider for review)
- **< 0.2**: Inactive (filtered from theme generation)

### Reactivation
- When old code receives new quotes in current analysis:
  - Reset `decay_score` to 1.0
  - Update `updated_at` to current timestamp
  - Code becomes active again for theme generation

### Filtering Rules
- Theme generation automatically filters codes where `decay_score < 0.2`
- Exception: Codes reactivated in current analysis window (received new quotes)
- Filtered codes remain in codebook (not deleted) for audit trail

## Snapshot Storage and Retrieval

### Storage Format
- JSON serialization in database `codebook_versions` table
- Compressed with gzip for versions > 1MB
- Indexed by `account_id` and `version` for fast retrieval

### Retrieval Patterns
- **Latest version**: `SELECT * FROM codebook_versions WHERE account_id = ? ORDER BY version DESC LIMIT 1`
- **Specific version**: `SELECT * FROM codebook_versions WHERE account_id = ? AND version = ?`
- **Version history**: `SELECT version, created_at, updated_at FROM codebook_versions WHERE account_id = ? ORDER BY version DESC`

### Compression Strategy
- For theme generation: Use LLMLingua if codebook > 100 codes or > 50k tokens
- Compression preserves: All `code_id`, at least 1 quote per code
- Compression is input-only; full codebook always stored uncompressed

## Quote ID Format

All quotes must use the canonical quote ID format defined in `models/quote_id@v1`:
- Simple: `{interaction_id}:ch_{chunk_index}:{start_pos}-{end_pos}`
- Email threads: `{interaction_id}:msg_{message_index}:ch_{chunk_index}:{start_pos}-{end_pos}`

See `models/quote_id/v1/CONTRACT.md` for full specification.

## Validation Rules

### Code Validation
- `label` must be non-empty and ≤ 200 characters
- `quotes` array must have at least 1 quote
- `decay_score` must be in range [0.0, 1.0]
- `code_id` must be valid UUID

### Quote Validation
- `quote_id` must match canonical regex pattern
- `text` must be non-empty
- `start_pos` < `end_pos`
- `chunk_index` ≥ 0

### Codebook Validation
- `version` must match pattern `^v\d+$`
- `codes` array can be empty (new account)
- `created_at` ≤ `updated_at`
