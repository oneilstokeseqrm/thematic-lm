# Agent Specs Summary

This document summarizes the four agent specification packages created for the Thematic-LM multi-agent pipeline.

## Created Specs

### 1. Coder Agent (`coder/`)
- **Purpose**: Generate codes with quotes from individual interactions
- **Key Features**:
  - Identity perspective support (multiple viewpoints)
  - Chunking strategy for long interactions
  - Quote ID encoding with canonical format
  - Cost tracking and DRY_RUN mode
- **Files**: requirements.md, DEPENDENCIES.yaml, design.md, tasks.md

### 2. Reviewer Agent (`reviewer/`)
- **Purpose**: Update adaptive codebook with new codes using semantic similarity
- **Key Features**:
  - OpenAI embeddings (text-embedding-3-large)
  - Pinecone vector similarity search
  - Code merging with similarity threshold (0.85)
  - Decay scoring algorithm
  - Codebook versioning and snapshots
- **Files**: requirements.md, DEPENDENCIES.yaml, design.md, tasks.md

### 3. Theme Coder Agents (`theme-coder-agents/`)
- **Purpose**: Generate theme proposals from codebook analysis
- **Key Features**:
  - Automatic compression for large codebooks (>100 codes or >50k tokens)
  - LLMLingua integration via LangChain DocumentCompressor
  - Fallback to simple truncation
  - Preservation rules (all code IDs + ≥1 quote per code)
  - GPT-4o theme generation
- **Files**: requirements.md, DEPENDENCIES.yaml, design.md, tasks.md

### 4. Theme Aggregator (`theme-aggregator/`)
- **Purpose**: Merge and curate final themes from multiple theme coder agents
- **Key Features**:
  - Semantic similarity detection (SequenceMatcher)
  - Theme merging with 0.80 similarity threshold
  - Quote consolidation with diversity preference
  - Quality thresholds (≥3 interactions per theme)
  - Output validation against models/themes@v1
- **Files**: requirements.md, DEPENDENCIES.yaml, design.md, tasks.md

## Spec Structure

Each spec follows the standard structure:

```
.kiro/specs/{agent-name}/
├── requirements.md      # User stories and acceptance criteria in EARS format
├── DEPENDENCIES.yaml    # Provides/consumes contracts and dependencies
├── design.md           # Architecture, classes, algorithms, error handling
└── tasks.md            # Implementation tasks with requirements traceability
```

## Contract Dependencies

### Provides
- `coder/` → `internal/agents-coder@v1`
- `reviewer/` → `models/codebook@v1`
- `theme-coder-agents/` → `internal/agents-theme-coder@v1`
- `theme-aggregator/` → `models/themes@v1`

### Consumes
- `coder/` consumes: `models/chunking@v1`, `models/quote_id@v1`
- `reviewer/` consumes: `internal/agents-coder@v1`, `models/codebook@v1`
- `theme-coder-agents/` consumes: `models/codebook@v1`
- `theme-aggregator/` consumes: `internal/agents-theme-coder@v1`, `models/quote_id@v1`

## Testing Strategy

All specs follow the testing standards from `.kiro/steering/testing-standards.md`:

### Unit Tests (No LIVE_TESTS)
- Pure logic with mocks
- Fast execution (<100ms per test)
- No external dependencies
- All agents have extensive unit test coverage

### Integration Tests (Requires LIVE_TESTS=1)
- **Coder**: OpenAI API calls for code generation
- **Reviewer**: OpenAI embeddings + Pinecone + Neon database
- **Theme Coder**: OpenAI API calls for theme generation
- **Theme Aggregator**: Pure logic (no LIVE_TESTS needed)

### DRY_RUN Mode
- All agents support DRY_RUN=1 for testing without API costs
- Mock responses match expected structure
- Useful for CI/CD pipelines

## Implementation Order

Recommended implementation order based on dependencies:

1. **Coder Agent** (no dependencies on other agents)
2. **Reviewer Agent** (depends on coder output)
3. **Theme Coder Agents** (depends on codebook from reviewer)
4. **Theme Aggregator** (depends on theme coder output)

## Key Design Decisions

### Coder Agent
- Identity perspectives enable multiple viewpoints on same data
- Chunking uses tiktoken cl100k_base (OpenAI GPT-4 tokenizer)
- Quote IDs use canonical format: `{interaction_id}:ch_{chunk_index}:{start_pos}-{end_pos}`

### Reviewer Agent
- Similarity threshold of 0.85 balances precision and recall
- Decay scoring uses exponential decay with usage factor
- Codebook snapshots enable versioning and rollback

### Theme Coder Agents
- Compression gate at 100 codes or 50k tokens
- LLMLingua provides intelligent compression with fallback
- Full codebook always preserved in storage (compression is input-only)

### Theme Aggregator
- Similarity threshold of 0.80 for theme merging
- Quality threshold of ≥3 interactions per theme
- Quote selection prioritizes diversity (different interactions)

## Next Steps

1. Review all specs for completeness and accuracy
2. Begin implementation starting with Coder Agent
3. Create integration tests as components are completed
4. Wire agents together in LangGraph pipeline
5. Test end-to-end workflow with small dataset

## Notes

- All specs align with existing contracts in `.kiro/contracts/`
- All specs follow code conventions from `.kiro/steering/code-conventions.md`
- All specs respect security policies from `.kiro/steering/security-policies.md`
- All specs include cost tracking and DRY_RUN support
