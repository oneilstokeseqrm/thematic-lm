---
spec_id: reviewer
name: Codebook Reviewer
version: 1.0.0
status: Draft
owners: ["@dev-team"]
provides:
  - models/codebook@v1
consumes:
  - internal/agents-code-aggregator@v1
  - models/quote_id@v1
---

# Requirements: Codebook Reviewer

## Introduction

The reviewer updates the codebook with new codes using embeddings and similarity search. It generates embeddings for codes, queries Pinecone for similar existing codes, and decides whether to merge or add new codes.

## Requirements

### Requirement 1: Embedding Generation

**User Story**: As a reviewer, I want to generate embeddings for codes, so that I can perform semantic similarity search.

#### Acceptance Criteria

1. WHEN receiving a new code, THE SYSTEM SHALL generate an embedding using OpenAI text-embedding-3-large model
2. WHEN generating embeddings, THE SYSTEM SHALL use the code label as input text
3. WHEN embedding generation succeeds, THE SYSTEM SHALL return a 3072-dimensional vector
4. WHEN embedding generation fails with a retriable error, THE SYSTEM SHALL retry up to 3 times with exponential backoff
5. WHEN LIVE_TESTS=1, THE SYSTEM SHALL use real OpenAI API calls for embedding generation
6. WHEN DRY_RUN=1, THE SYSTEM SHALL return mock embeddings without calling the API

### Requirement 2: Pinecone Similarity Search

**User Story**: As a reviewer, I want to find similar existing codes, so that I can decide whether to merge or add new codes.

#### Acceptance Criteria

1. WHEN searching for similar codes, THE SYSTEM SHALL query Pinecone with the code embedding
2. WHEN querying Pinecone, THE SYSTEM SHALL retrieve top-5 most similar codes (k=5)
3. WHEN querying Pinecone, THE SYSTEM SHALL filter by account_id to enforce tenant isolation
4. WHEN Pinecone returns results, THE SYSTEM SHALL include similarity scores (cosine similarity)
5. WHEN LIVE_TESTS=1, THE SYSTEM SHALL use real Pinecone API calls
6. WHEN no similar codes exist, THE SYSTEM SHALL return empty results (valid case)

### Requirement 3: Code Merging Logic

**User Story**: As a reviewer, I want to merge similar codes intelligently, so that the codebook stays concise without losing information.

#### Acceptance Criteria

1. WHEN a similar code exists with similarity > 0.85, THE SYSTEM SHALL merge the new code into the existing code
2. WHEN merging codes, THE SYSTEM SHALL keep the existing code_id (stability)
3. WHEN merging codes, THE SYSTEM SHALL append new quotes to the existing code's quotes array
4. WHEN merging codes, THE SYSTEM SHALL update the existing code's updated_at timestamp
5. WHEN merging codes, THE SYSTEM SHALL reset decay_score to 1.0 (reactivation)
6. WHEN no similar code exists (similarity ≤ 0.85), THE SYSTEM SHALL add the new code with a new code_id

### Requirement 4: Codebook Snapshot Creation

**User Story**: As a reviewer, I want to create codebook snapshots, so that I can track codebook evolution over time.

#### Acceptance Criteria

1. WHEN all codes are processed, THE SYSTEM SHALL create a new codebook version (e.g., v43)
2. WHEN creating a snapshot, THE SYSTEM SHALL persist the full codebook to database (codebook_versions table)
3. WHEN creating a snapshot, THE SYSTEM SHALL include version, account_id, codes, created_at, updated_at fields
4. WHEN creating a snapshot, THE SYSTEM SHALL increment version number from previous version
5. WHEN LIVE_TESTS=1, THE SYSTEM SHALL persist to real database with RLS enforcement

### Requirement 5: Decay Scoring Updates

**User Story**: As a reviewer, I want to update decay scores, so that inactive codes are filtered from theme generation.

#### Acceptance Criteria

1. WHEN a code receives new quotes, THE SYSTEM SHALL reset its decay_score to 1.0 (reactivation)
2. WHEN a code is not updated, THE SYSTEM SHALL calculate decay_score using time_decay_factor and usage_factor
3. WHEN calculating decay, THE SYSTEM SHALL use formula: decay_score = base_score × exp(-λ × days_since_last_update) × min(1.0, quote_count / 10)
4. WHEN decay_score < 0.2, THE SYSTEM SHALL mark the code as inactive (filtered from theme generation)
5. WHEN a previously inactive code is reactivated, THE SYSTEM SHALL reset decay_score to 1.0

### Requirement 6: Pinecone Index Management

**User Story**: As a reviewer, I want to upsert code embeddings to Pinecone, so that future similarity searches include new codes.

#### Acceptance Criteria

1. WHEN adding a new code, THE SYSTEM SHALL upsert the code embedding to Pinecone with metadata (code_id, account_id, label)
2. WHEN merging codes, THE SYSTEM SHALL update the existing code's embedding in Pinecone
3. WHEN upserting to Pinecone, THE SYSTEM SHALL include account_id in metadata for tenant isolation
4. WHEN Pinecone upsert fails with a retriable error, THE SYSTEM SHALL retry up to 3 times
5. WHEN LIVE_TESTS=1, THE SYSTEM SHALL use real Pinecone API calls

### Requirement 7: Batch Processing

**User Story**: As a reviewer, I want to process codes in batches, so that I can optimize API calls and performance.

#### Acceptance Criteria

1. WHEN generating embeddings for multiple codes, THE SYSTEM SHALL batch requests (up to 100 codes per batch)
2. WHEN upserting to Pinecone, THE SYSTEM SHALL batch upserts (up to 100 vectors per batch)
3. WHEN batch processing fails partially, THE SYSTEM SHALL log errors and continue with successful items
4. WHEN all batches complete, THE SYSTEM SHALL return the updated codebook

### Requirement 8: Cost Tracking

**User Story**: As a system operator, I want to track embedding generation costs, so that I can monitor API usage.

#### Acceptance Criteria

1. WHEN generating embeddings, THE SYSTEM SHALL record token usage (input tokens)
2. WHEN embedding generation completes, THE SYSTEM SHALL calculate cost (tokens × embedding model pricing)
3. WHEN reviewer completes, THE SYSTEM SHALL return total embedding cost in metadata
