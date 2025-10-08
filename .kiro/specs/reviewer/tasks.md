# Implementation Tasks: Codebook Reviewer

## Task List

- [ ] 1. Create ReviewerAgent class structure
  - Define `__init__` with OpenAI, Pinecone clients, similarity threshold
  - Add `update_codebook` method signature
  - Add helper methods for embedding, similarity search, merging
  - _Requirements: REV-REQ-001, REV-REQ-002, REV-REQ-003_

- [ ] 2. Implement embedding generation
  - Configure OpenAI client for text-embedding-3-large
  - Implement `_generate_embedding` method
  - Add error handling and retry logic
  - Write unit tests with mock OpenAI responses
  - _Requirements: REV-REQ-001_

- [ ] 3. Implement batch embedding generation
  - Create `_generate_embeddings_batch` for up to 100 codes
  - Handle partial batch failures
  - Write unit tests for batch processing
  - _Requirements: REV-REQ-007_

- [ ] 4. Configure Pinecone index
  - Create index setup script (one-time operation)
  - Configure dimension=3072, metric=cosine
  - Add metadata indexing for account_id, code_id
  - Document index configuration
  - _Requirements: REV-REQ-002, REV-REQ-006_
  - _Note: Requires Pinecone API; run manually or gate with LIVE_TESTS=1_

- [ ] 5. Implement Pinecone similarity search
  - Implement `_find_similar_codes` with top-k query
  - Add account_id filter for tenant isolation
  - Use namespace=account_id for additional isolation
  - Write integration test with real Pinecone (LIVE_TESTS=1)
  - _Requirements: REV-REQ-002_
  - _Note: Requires LIVE_TESTS=1 for Pinecone_

- [ ] 6. Implement code merging logic
  - Implement `_merge_code` to update existing code
  - Keep existing code_id (stability)
  - Append new quotes to existing quotes array
  - Update updated_at timestamp
  - Reset decay_score to 1.0
  - Write unit tests for merging
  - _Requirements: REV-REQ-003_

- [ ] 7. Implement new code creation
  - Implement `_create_new_code` with new UUID
  - Set initial decay_score = 1.0
  - Set created_at and updated_at timestamps
  - Write unit tests
  - _Requirements: REV-REQ-003_

- [ ] 8. Implement decay score calculation
  - Create `calculate_decay_score` function
  - Use formula: exp(-λ × days) × min(1.0, quotes/10)
  - Default λ = 0.01 (configurable)
  - Write unit tests with various time deltas
  - _Requirements: REV-REQ-005_

- [ ] 9. Implement decay score updates
  - Update decay scores for all existing codes
  - Reset to 1.0 for codes receiving new quotes
  - Mark codes with score < 0.2 as inactive
  - Write unit tests for reactivation logic
  - _Requirements: REV-REQ-005_

- [ ] 10. Implement Pinecone upsert
  - Implement `_upsert_embedding` with metadata
  - Include account_id, code_id, label in metadata
  - Use namespace=account_id
  - Add retry logic for failures
  - Write integration test (LIVE_TESTS=1)
  - _Requirements: REV-REQ-006_
  - _Note: Requires LIVE_TESTS=1 for Pinecone_

- [ ] 11. Implement batch Pinecone upsert
  - Batch up to 100 vectors per upsert
  - Handle partial failures
  - Write integration test (LIVE_TESTS=1)
  - _Requirements: REV-REQ-007_
  - _Note: Requires LIVE_TESTS=1 for Pinecone_

- [ ] 12. Implement version increment logic
  - Parse current version (e.g., "v42")
  - Increment version number
  - Return new version string (e.g., "v43")
  - Write unit tests
  - _Requirements: REV-REQ-004_

- [ ] 13. Create codebook_versions table migration
  - Define table schema with version, account_id, codebook JSONB
  - Add RLS policy for tenant isolation
  - Add indexes on (account_id, version)
  - Test migration with Alembic
  - _Requirements: REV-REQ-004_
  - _Note: Requires LIVE_TESTS=1 for database_

- [ ] 14. Implement codebook snapshot persistence
  - Serialize codebook to JSON
  - Insert into codebook_versions table
  - Set app.current_account_id session variable
  - Write integration test (LIVE_TESTS=1)
  - _Requirements: REV-REQ-004_
  - _Note: Requires LIVE_TESTS=1 for database_

- [ ] 15. Implement codebook loading
  - Query latest version for account_id
  - Deserialize JSON to codebook structure
  - Handle case: no existing codebook (new account)
  - Write integration test (LIVE_TESTS=1)
  - _Requirements: REV-REQ-004_
  - _Note: Requires LIVE_TESTS=1 for database_

- [ ] 16. Add cost tracking
  - Record token usage for embedding generation
  - Calculate embedding costs
  - Return total cost in metadata
  - _Requirements: REV-REQ-008_

- [ ] 17. Add DRY_RUN mode support
  - Check DRY_RUN environment variable
  - Return mock embeddings if DRY_RUN=1
  - Skip Pinecone operations if DRY_RUN=1
  - Test both modes
  - _Requirements: REV-REQ-001, REV-REQ-002_

- [ ] 18. Write integration test for full reviewer flow
  - Test with aggregated codes
  - Verify embeddings generated
  - Verify Pinecone similarity search
  - Verify codebook updated and persisted
  - Gate with LIVE_TESTS=1
  - _Requirements: All requirements_
  - _Note: Requires LIVE_TESTS=1 for OpenAI, Pinecone, database_

- [ ] 19. Write integration test for decay scoring
  - Test with codes at various ages
  - Verify decay scores calculated correctly
  - Verify reactivation on new quotes
  - Verify inactive codes marked (score < 0.2)
  - _Requirements: REV-REQ-005_

- [ ] 20. Write integration test for tenant isolation
  - Test with multiple accounts
  - Verify Pinecone queries filter by account_id
  - Verify RLS enforcement on codebook_versions
  - Gate with LIVE_TESTS=1
  - _Requirements: REV-REQ-002, REV-REQ-004_
  - _Note: Requires LIVE_TESTS=1 for Pinecone and database_
