# Implementation Tasks: Theme Aggregator

## Task List

- [ ] 1. Create ThemeAggregator class structure
  - Define `__init__` with configurable thresholds (similarity, min_interactions, max_quotes)
  - Add `aggregate_themes` method signature
  - Add helper methods: `_merge_similar_themes`, `_consolidate_quotes`, `_apply_quality_thresholds`
  - _Requirements: AGG-REQ-001, AGG-REQ-002, AGG-REQ-003_

- [ ] 2. Implement semantic similarity detection
  - Implement `_are_themes_similar` using SequenceMatcher
  - Use weighted average (70% title, 30% description)
  - Set default similarity threshold to 0.80
  - Add logging for similarity scores
  - _Requirements: AGG-REQ-001_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 3. Implement theme merging logic
  - Implement `_merge_similar_themes` to group similar themes
  - Implement `_merge_theme_group` to combine theme data
  - Select best title and description (most descriptive)
  - Combine quotes and code_ids from all similar themes
  - _Requirements: AGG-REQ-001_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 4. Write unit tests for theme merging
  - Test similarity detection with various title/description pairs
  - Test merging with different similarity thresholds
  - Test with no similar themes (all unique)
  - Test with all similar themes (merge into one)
  - _Requirements: AGG-REQ-001_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 5. Implement quote deduplication
  - Implement `_deduplicate_quotes` using quote_id
  - Handle missing quote_ids gracefully
  - Preserve quote order where possible
  - Add logging for duplicate counts
  - _Requirements: AGG-REQ-002_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 6. Implement quote selection strategy
  - Implement `_select_best_quotes` with diversity preference
  - Group quotes by interaction_id for diversity
  - Select shortest/clearest quote per interaction
  - Limit to max_quotes_per_theme (default 5)
  - _Requirements: AGG-REQ-002_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 7. Write unit tests for quote consolidation
  - Test deduplication with duplicate quote_ids
  - Test selection with various quote distributions
  - Test diversity preference (different interactions)
  - Test with more quotes than max_quotes_per_theme
  - _Requirements: AGG-REQ-002_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 8. Implement quality threshold checks
  - Implement `_meets_quality_threshold` method
  - Implement `_count_unique_interactions` for minimum interaction check
  - Implement `_is_generic_title` to detect generic titles
  - Check description quality (non-empty, min length)
  - _Requirements: AGG-REQ-003_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 9. Implement quality filtering
  - Implement `_apply_quality_thresholds` to filter themes
  - Log warnings for excluded themes with reasons
  - Use configurable MIN_INTERACTIONS_PER_THEME (default 3)
  - Handle edge case of all themes failing quality checks
  - _Requirements: AGG-REQ-003_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 10. Write unit tests for quality validation
  - Test with themes meeting all quality criteria
  - Test with themes below minimum interactions
  - Test with generic titles (e.g., "Theme 1")
  - Test with empty or short descriptions
  - _Requirements: AGG-REQ-003_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 11. Implement output structure creation
  - Implement `_create_themes_output` method
  - Generate theme_id (UUID) for each theme
  - Include all required metadata (analysis_id, account_id, codebook_version, created_at)
  - Format created_at as ISO 8601 with Z suffix
  - _Requirements: AGG-REQ-004, AGG-REQ-005_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 12. Implement output validation
  - Implement `_validate_output` against models/themes@v1 schema
  - Check all required top-level fields
  - Validate each theme structure (theme_id, title, description, quotes, code_ids)
  - Validate each quote structure (quote_id, text, interaction_id)
  - _Requirements: AGG-REQ-005_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 13. Write unit tests for output creation
  - Test output structure matches models/themes@v1
  - Test with empty themes array (valid case)
  - Test with multiple themes
  - Test validation catches missing required fields
  - _Requirements: AGG-REQ-004, AGG-REQ-005_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 14. Add codebook version linking
  - Verify codebook_version is included in output
  - Add optional validation that codebook_version exists (if DB access available)
  - Add optional validation that code_ids exist in codebook (if DB access available)
  - Log warnings for invalid references but continue processing
  - _Requirements: AGG-REQ-004_
  - _Note: Core logic doesn't need LIVE_TESTS, optional DB validation does_

- [ ] 15. Implement error handling
  - Handle empty theme proposals (return empty themes array)
  - Handle malformed theme structures (skip and log)
  - Handle validation failures (log detailed errors)
  - Handle missing required fields gracefully
  - _Requirements: All requirements_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 16. Add performance optimization
  - Profile merging algorithm with large theme sets (50+ themes)
  - Optimize similarity comparisons if needed
  - Add progress logging for large theme sets
  - Document performance characteristics
  - _Requirements: AGG-REQ-006_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 17. Write comprehensive integration test
  - Test full aggregation workflow with realistic data
  - Include multiple theme proposals from different agents
  - Test with similar themes, unique themes, and low-quality themes
  - Verify output matches models/themes@v1 contract
  - _Requirements: All requirements_
  - _Note: Pure logic, no LIVE_TESTS needed_

- [ ] 18. Add configuration support
  - Support MIN_INTERACTIONS_PER_THEME environment variable
  - Support similarity_threshold configuration
  - Support max_quotes_per_theme configuration
  - Document all configuration options
  - _Requirements: AGG-REQ-003, AGG-REQ-006_
  - _Note: Pure logic, no LIVE_TESTS needed_
