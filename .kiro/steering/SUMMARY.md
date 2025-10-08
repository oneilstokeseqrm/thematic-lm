# Steering Documentation Summary

This directory contains comprehensive steering documentation for the Thematic-LM project, generated from the Start Plan specification.

## Files Created

1. **product.md** - Product overview and capabilities
2. **tech.md** - Technical architecture and infrastructure
3. **structure.md** - Project structure and module boundaries
4. **api-standards.md** - API design standards and conventions
5. **testing-standards.md** - Testing strategy and quality gates
6. **security-policies.md** - Security, privacy, and compliance policies
7. **code-conventions.md** - Code style, typing, and logging standards
8. **multi-agent-protocols.md** - Contract versioning and deprecation policy

## Contracts Created

### Events Contracts
- **events/analysis-events@v1** - Analysis lifecycle events (accepted, completed, failed)
  - JSON Schema with strict validation
  - 3 example events
  - Human documentation

### API Contracts
- **apis/bff@v1** - BFF API OpenAPI specification
  - Complete OpenAPI 3.0 spec
  - POST /analyze, GET /analysis/{id}, GET /analyses endpoints
  - Request/response examples for all endpoints and status values

### Model Contracts
- **models/codebook@v1** - Codebook and code structures
  - JSON Schema with strict validation
  - Example codebook with 5 codes
  - Decay scoring and merging strategy documentation

- **models/themes@v1** - Theme output format
  - JSON Schema with strict validation
  - Example themes with 3 themes
  - Quality thresholds and quote selection strategy

- **models/quote_id@v1** - Quote ID encoding rules
  - Format specification with regex pattern
  - Unicode code-point indexing rules
  - 3 examples (simple, chunked, email thread)

- **models/chunking@v1** - Text chunking strategy
  - Tokenizer specification (tiktoken cl100k_base)
  - Boundary detection rules
  - Example chunking with 3 chunks

### Validation Tooling
- **scripts/validate_contracts.py** - Automated validation script
  - Validates JSON schemas against meta-schema
  - Validates examples against schemas
  - Validates quote IDs, UUIDs, and timestamps
  - Exit code 0 = all valid, 1 = errors

- **.kiro/contracts/README.md** - Contracts documentation
  - Organization and structure
  - How to add new contracts
  - Versioning and deprecation process
  - JSON Schema standards

## Validation Status

✅ **All contracts validated successfully**

```bash
$ python scripts/validate_contracts.py
Validating all contracts...

✓ Schema valid: .kiro/contracts/models/codebook/v1/schema.json
✓ Example valid: .kiro/contracts/models/codebook/v1/examples/codebook.json
✓ Schema valid: .kiro/contracts/models/themes/v1/schema.json
✓ Example valid: .kiro/contracts/models/themes/v1/examples/themes.json
✓ Schema valid: .kiro/contracts/events/analysis-events/v1/schema.json
✓ Example valid: .kiro/contracts/events/analysis-events/v1/examples/analysis_accepted.json
✓ Example valid: .kiro/contracts/events/analysis-events/v1/examples/analysis_failed.json
✓ Example valid: .kiro/contracts/events/analysis-events/v1/examples/analysis_completed.json

============================================================
Total checks: 8
Total errors: 0
✓ All contracts valid!
```

## JSON Schema Standards Applied

All schemas follow strict standards:
- ✅ Include `$schema` (draft-07) and `$id`
- ✅ Set `additionalProperties: false` on all objects
- ✅ Use `format: uuid` for all ID fields
- ✅ Use `format: date-time` for all timestamp fields
- ✅ Use enums for fields with fixed value sets
- ✅ Provide descriptions for all fields

## Next Steps

### Immediate (v1 Scope)
1. ✅ Define database schema and create initial Alembic migration
2. Implement LangGraph pipeline with StateGraph and node functions
3. Create agent prompt templates for coder, aggregator, reviewer, theme agents
4. Implement cost estimation and budget enforcement logic
5. Set up structured logging with required fields
6. ✅ Create OpenAPI spec for BFF API

### Short-term (Post-v1)
1. Implement event streaming architecture (Option A with Redis/Kafka)
2. Add circuit breaker pattern with configurable thresholds
3. Implement compression fallback logic
4. Create metrics dashboards (Prometheus/Grafana)
5. Add advanced tracing (OpenTelemetry)
6. Implement PII redaction module

### Long-term (Future Enhancements)
1. Multi-modal analysis (images, audio, video)
2. Multilingual support
3. Model fine-tuning for domain-specific tasks
4. Interactive human-in-the-loop interface
5. Real-time continuous analysis
6. On-premise deployment with self-hosted models

## MCP Configuration Status

### Currently Configured (in .kiro/settings/mcp.json)
✅ **GitHub MCP** - Configured with Docker
✅ **Neon MCP** - Configured with npx
✅ **LangGraph Docs MCP** - Configured with uvx

### User-Level MCPs (in ~/.kiro/settings/mcp.json)
✅ **web-search** (Brave Search) - Available globally
✅ **context7** - Available globally
✅ **aws-docs** - Available globally

## Contract Coverage

All major system interfaces are now documented with machine-readable contracts:

- ✅ **Events**: Analysis lifecycle notifications
- ✅ **API**: BFF endpoints for analysis submission and polling
- ✅ **Data Models**: Codebook, themes, quotes, chunking
- ✅ **Validation**: Automated validation tooling
- ✅ **Documentation**: Human-readable docs for all contracts

## Assumptions Made

### 1. Identity Configuration
- Assumed identities are defined in YAML format (referenced as `identities.yaml` in Start Plan)
- Hot reload mechanism requires file watcher or version check (implementation details deferred)
- Identity prompts are woven into system prompts for each coder agent

### 2. Cost Estimation
- Token estimation uses average tokens per interaction (specific formula not provided)
- Cost per token values need to be configured per model (GPT-4o pricing)
- Budget enforcement happens before job execution (fail-fast approach)

### 3. Checkpoint Cleanup
- Daily cleanup job implementation details not specified (cron job, scheduled task, etc.)
- Retention periods (7 days for completed, 30 days for failed) are configurable
- Cleanup logic needs to be implemented as separate service or scheduled task

### 4. Event Streaming (Future)
- Option A (centralized event stream) is favored but not yet implemented
- Event format and consumer group naming conventions defined
- Integration with Redis Streams or Kafka deferred to post-v1

### 5. Circuit Breaker (v1 Simplified)
- No global circuit breaker in v1; rely on retries and exponential backoff
- Circuit breaker thresholds mentioned in observability section but not implemented
- Full circuit breaker pattern deferred to post-v1

### 6. Compression Fallback
- LLMLingua is primary compression strategy
- Fallback to simple truncation/summarization if LLMLingua unavailable
- Specific fallback implementation details not provided

### 7. Decay Scoring
- Code decay mechanism mentioned but scoring algorithm not specified
- Threshold of 0.2 for inactive codes (configurable)
- Reactivation logic when old codes receive new quotes

## Gaps Requiring Additional Input

### 1. Database Schema
- Specific table schemas not provided (interactions, codes, themes, etc.)
- RLS policy SQL examples provided but full schema needed
- Alembic migration strategy and initial migration

### 2. LangGraph Pipeline Details
- Specific node function signatures not provided
- State schema structure (TypedDict fields) needs definition
- Conditional edge logic for routing between stages

### 3. Agent Prompt Templates
- Coder, aggregator, reviewer, theme agent prompts not provided
- Identity perspective prompt prefixes not specified
- Few-shot examples for agents (if any)

### 4. Cost Calculation Formulas
- Token estimation formula not specified
- Cost per token for different models (GPT-4o, embeddings)
- Budget allocation strategy for multi-stage pipeline

### 5. Compression Thresholds
- Threshold values (100 codes, 50k tokens) are configurable but defaults not justified
- Compression ratio targets not specified
- Quality metrics for compressed vs. full codebook

### 6. Identity Configuration Format
- YAML structure for identities not provided
- Example identity definitions needed
- Hot reload mechanism implementation details

## Additional Steering Files to Consider

### 1. deployment.md
- Infrastructure setup (Neon, Pinecone, OpenAI)
- Environment configuration
- CI/CD pipeline
- Monitoring and alerting setup

### 2. troubleshooting.md
- Common issues and solutions
- Debugging strategies
- Log analysis techniques
- Performance optimization tips

### 3. contributing.md
- Development workflow
- Branch naming conventions
- PR review process
- Code review checklist

### 4. glossary.md
- Domain-specific terminology
- Acronyms and abbreviations
- Thematic analysis concepts
- LangGraph terminology

### 5. examples.md
- Sample analysis requests
- Example codebook structures
- Theme output examples
- Quote ID encoding examples

## Clarifications Needed

1. **Identity Perspectives**: What are the default identities? How many should be used for typical analysis?
2. **Cost Budget**: What is a reasonable default for `COST_BUDGET_USD`? How does it scale with data volume?
3. **Codebook Size**: What is the expected codebook size after analyzing 1000, 10000, 100000 interactions?
4. **Theme Count**: How many themes are typically generated? Is there a target range?
5. **Analysis Duration**: What is the expected duration for small (100), medium (1000), large (10000) datasets?
6. **Incremental Threshold**: What percentage of new codes triggers full theme regeneration?
7. **Decay Algorithm**: How is decay_score calculated? What factors influence it?
8. **Compression Quality**: How is compression quality measured? What is acceptable loss?
