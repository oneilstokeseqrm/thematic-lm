# Implementation Tasks: Code Aggregator

## Task List

- [ ] 1. Create CodeAggregator class structure
  - Define `__init__` with similarity_threshold parameter (default 0.85)
  - Add `aggregate_codes` method signature
  - Add helper methods: `_merge_similar_codes`, `_are_similar`, `_merge_code_group`
  - _Requirements: AGG-REQ-001_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 2. Implement similarity detection
  - Use `difflib.SequenceMatcher` for fuzzy string matching
  - Implement `_are_similar` method with threshold check
  - Handle case-insensitive comparison
  - Write unit tests with various label pairs
  - _Requirements: AGG-REQ-001_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 3. Implement code merging logic
  - Implement `_merge_similar_codes` to find and group similar codes
  - Track used indices to avoid duplicate merging
  - Handle edge case: single code (no merging needed)
  - Write unit tests with various code combinations
  - _Requirements: AGG-REQ-001_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 4. Implement label selection
  - Select longest label as most descriptive
  - Preserve original wording (no rewriting)
  - Handle tie-breaking (same length labels)
  - Write unit tests for label selection
  - _Requirements: AGG-REQ-001_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 5. Implement quote preservation
  - Combine quotes arrays from all merged codes
  - Deduplicate by quote_id (exact match)
  - Maintain quote order
  - Write unit tests for quote deduplication
  - _Requirements: AGG-REQ-002_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 6. Implement quote_id deduplication
  - Use set to track seen quote_ids
  - Skip quotes with duplicate quote_ids
  - Preserve first occurrence of each quote_id
  - Write unit tests with duplicate quote_ids
  - _Requirements: AGG-REQ-002_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 7. Handle identity diversity
  - Test merging codes from different identities
  - Verify similar concepts merge regardless of identity
  - Verify different concepts stay separate
  - Write unit tests with multi-identity scenarios
  - _Requirements: AGG-REQ-003_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 8. Add error handling
  - Handle empty codes list (return empty list)
  - Handle missing quotes field (log warning, use empty array)
  - Handle invalid quote_id format (log warning, skip quote)
  - Write unit tests for error cases
  - _Requirements: AGG-REQ-001, AGG-REQ-002_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 9. Write integration test with realistic data
  - Test with codes from 3 identities (objective, empathy, critical)
  - Include duplicate codes, similar codes, and unique codes
  - Verify correct merging and quote preservation
  - Verify output structure matches expected format
  - _Requirements: All requirements_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 10. Add performance optimization
  - Profile pairwise comparison performance
  - Add early termination when similarity found
  - Document O(n²) complexity and acceptable scale
  - Test with large code lists (100+ codes)
  - _Requirements: AGG-REQ-001_
  - _Note: Pure logic, no LIVE_TESTS needed_
