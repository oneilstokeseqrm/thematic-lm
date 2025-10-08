# Implementation Tasks: Theme Coder Agents

## Task List

- [ ] 1. Create ThemeCoderAgent class structure
  - Define `__init__` with OpenAI client and threshold parameters
  - Add `generate_themes` method signature
  - Add helper methods: `_needs_compression`, `_compress_codebook`, `_generate_themes_llm`
  - Initialize tiktoken tokenizer with cl100k_base encoding
  - _Requirements: THEME-REQ-001, THEME-REQ-005_

- [ ] 2. Implement compression gate logic
  - Implement `_needs_compression` with code count and token thresholds
  - Use tiktoken cl100k_base for token counting
  - Implement `_codebook_to_text` for token calculation
  - Add logging for compression decisions (triggered/skipped with metrics)
  - _Requirements: THEME-REQ-001_

- [ ] 3. Write unit tests for compression gate
  - Test with codebooks below thresholds (no compression)
  - Test with codebooks above code threshold (>100 codes)
  - Test with codebooks above token threshold (>50k tokens)
  - Test token counting accuracy with tiktoken
  - _Requirements: THEME-REQ-001_

- [ ] 4. Implement LLMLingua integration
  - Install and configure LLMLingua via LangChain DocumentCompressor
  - Implement `_compress_with_llmlingua` method
  - Convert codebook to LangChain Documents format
  - Preserve all code IDs and at least 1 quote per code
  - Handle LLMLingua initialization failures gracefully
  - _Requirements: THEME-REQ-002, THEME-REQ-004_

- [ ] 5. Implement fallback compression
  - Implement `_compress_with_truncation` method
  - Use identical preservation rules (all code IDs + ≥1 quote per code)
  - Implement `_select_best_quote` to choose representative quotes (prefer shorter)
  - Add token-based truncation logic
  - Log fallback usage for monitoring
  - _Requirements: THEME-REQ-003, THEME-REQ-004_

- [ ] 6. Write unit tests for compression methods
  - Test LLMLingua compression with mock DocumentCompressor
  - Test fallback truncation with various codebook sizes
  - Test preservation rules (all code IDs + ≥1 quote per code)
  - Test quote selection logic (shortest quote preferred)
  - Test compression verification (all codes have ≥1 quote)
  - _Requirements: THEME-REQ-002, THEME-REQ-003, THEME-REQ-004_

- [ ] 7. Implement theme generation prompt template
  - Create THEME_GENERATION_PROMPT with JSON response format
  - Implement `_format_codebook_for_prompt` method
  - Add instructions for 3-8 themes with titles, descriptions, quotes, code IDs
  - Include example response format in prompt
  - _Requirements: THEME-REQ-005_

- [ ] 8. Implement LLM integration for theme generation
  - Configure OpenAI client with GPT-4o model
  - Implement `_generate_themes_llm` method
  - Add JSON response parsing with error handling
  - Set low temperature (0.1) for consistency
  - _Requirements: THEME-REQ-005_
  - _Note: Requires LIVE_TESTS=1 for real OpenAI API calls_

- [ ] 9. Write unit tests for theme generation
  - Test prompt formatting with various codebook structures
  - Test JSON response parsing with valid and invalid responses
  - Test with mock LLM responses
  - Test error handling for malformed JSON
  - _Requirements: THEME-REQ-005_

- [ ] 10. Implement full codebook preservation
  - Ensure compression only affects input to theme generation
  - Discard compressed version after theme generation
  - Verify original codebook remains unchanged
  - Add memory cleanup after processing
  - _Requirements: THEME-REQ-006_

- [ ] 11. Add cost tracking
  - Record prompt_tokens and completion_tokens from LLM response
  - Calculate theme generation cost (tokens × model pricing)
  - Return token usage and cost in output metadata
  - Integrate with cost-manager component
  - _Requirements: THEME-REQ-007_

- [ ] 12. Implement retry logic for LLM calls
  - Add exponential backoff for retriable errors (timeout, 5xx)
  - Max 3 retries per theme generation call
  - Log retry attempts with error details
  - Fail after max retries exceeded
  - _Requirements: THEME-REQ-008_

- [ ] 13. Implement automatic fallback handling
  - Wrap LLMLingua calls with try-catch
  - Automatically fall back to truncation on LLMLingua failure
  - Log fallback activation with reason
  - Ensure fallback uses same preservation rules
  - _Requirements: THEME-REQ-008_

- [ ] 14. Add DRY_RUN mode support
  - Check DRY_RUN environment variable
  - Return mock themes if DRY_RUN=1
  - Use real compression and LLM if DRY_RUN=0
  - Ensure mock themes match expected structure
  - _Requirements: THEME-REQ-005_

- [ ] 15. Write integration test with compression
  - Test with large codebook requiring compression (>100 codes)
  - Verify compression gate triggers correctly
  - Test both LLMLingua and fallback compression paths
  - Verify preservation rules are followed (all code IDs + ≥1 quote)
  - _Requirements: THEME-REQ-001, THEME-REQ-002, THEME-REQ-003, THEME-REQ-004_
  - _Note: Requires LLMLingua installation_

- [ ] 16. Write integration test with real LLM
  - Test theme generation with real OpenAI API
  - Use small codebook (10-20 codes) to minimize cost
  - Verify themes structure and content quality
  - Test with both compressed and uncompressed codebooks
  - Verify cost tracking accuracy
  - _Requirements: THEME-REQ-005, THEME-REQ-007_
  - _Note: Requires LIVE_TESTS=1 for real OpenAI API calls_

- [ ] 17. Add error handling for edge cases
  - Handle empty codebook (return empty themes)
  - Handle codebook with no quotes (use code labels only)
  - Handle LLMLingua installation failures
  - Handle malformed codebook structure
  - Log all errors with sufficient context for debugging
  - _Requirements: THEME-REQ-008_

- [ ] 18. Write comprehensive integration test
  - Test full theme generation workflow
  - Include compression gate, LLMLingua/fallback, and theme generation
  - Test with realistic codebook (50+ codes)
  - Verify output matches internal/agents-theme-coder@v1 contract
  - Test error recovery (LLMLingua failure → fallback → success)
  - _Requirements: All requirements_
  - _Note: Requires LIVE_TESTS=1 for LLM calls, LLMLingua for compression_
