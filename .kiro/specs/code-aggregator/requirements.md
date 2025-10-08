---
spec_id: code-aggregator
name: Code Aggregator
version: 1.0.0
status: Draft
owners: ["@dev-team"]
provides:
  - internal/agents-code-aggregator@v1
consumes:
  - internal/agents-coder@v1
---

# Requirements: Code Aggregator

## Introduction

The code aggregator deduplicates and merges codes from multiple coder agents while preserving all quotes and handling identity diversity.

## Requirements

### Requirement 1: Code Deduplication

**User Story**: As an aggregator, I want to identify duplicate codes, so that the final code list is concise.

#### Acceptance Criteria

1. WHEN receiving codes from multiple agents with identical labels, THE SYSTEM SHALL merge them into a single code
2. WHEN merging codes, THE SYSTEM SHALL preserve all quotes from both codes
3. WHEN codes have similar but not identical labels, THE SYSTEM SHALL use fuzzy matching (similarity > 0.85) to detect duplicates
4. WHEN codes are below similarity threshold, THE SYSTEM SHALL keep them as separate codes

### Requirement 2: Quote Preservation

**User Story**: As an aggregator, I want to preserve all quotes, so that no evidence is lost during merging.

#### Acceptance Criteria

1. WHEN merging codes, THE SYSTEM SHALL combine quotes arrays from all source codes
2. WHEN quotes have duplicate quote_ids, THE SYSTEM SHALL deduplicate by quote_id
3. WHEN merging completes, THE SYSTEM SHALL ensure each code has at least 1 quote

### Requirement 3: Identity Diversity Handling

**User Story**: As an aggregator, I want to handle codes from different identity perspectives, so that diverse viewpoints are preserved.

#### Acceptance Criteria

1. WHEN codes from different identities describe the same concept, THE SYSTEM SHALL merge them
2. WHEN codes from different identities describe different concepts, THE SYSTEM SHALL keep them separate
3. WHEN merging codes from different identities, THE SYSTEM SHALL select the most descriptive label
