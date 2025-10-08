# Multi-Agent Protocols

## Active Contracts

Contracts are stored in `.kiro/contracts/` and define the interfaces between agents, pipeline stages, and external systems.

### Events Contracts

- **events/analysis-events@v1** - Analysis lifecycle events (Active)
  - Purpose: Event schemas for analysis pipeline (accepted, completed, failed)
  - Schema: `.kiro/contracts/events/analysis-events/v1/schema.json`
  - Documentation: `.kiro/contracts/events/analysis-events/v1/CONTRACT.md`
  - Status: Active, stable

### API Contracts

- **apis/bff@v1** - BFF API endpoints (Active)
  - Purpose: OpenAPI specification for Backend-For-Frontend API
  - Schema: `.kiro/contracts/apis/bff/v1/openapi.yaml`
  - Endpoints: POST /analyze, GET /analysis/{id}, GET /analyses
  - Status: Active, stable

### Model Contracts

- **models/codebook@v1** - Codebook and code structures (Active)
  - Purpose: Adaptive codebook data structure with codes and quotes
  - Schema: `.kiro/contracts/models/codebook/v1/schema.json`
  - Documentation: `.kiro/contracts/models/codebook/v1/CONTRACT.md`
  - Status: Active, stable

- **models/themes@v1** - Theme output format (Active)
  - Purpose: Theme generation output with supporting quotes and code references
  - Schema: `.kiro/contracts/models/themes/v1/schema.json`
  - Documentation: `.kiro/contracts/models/themes/v1/CONTRACT.md`
  - Status: Active, stable

- **models/quote_id@v1** - Quote ID encoding rules (Active)
  - Purpose: Quote identifier format and validation rules
  - Documentation: `.kiro/contracts/models/quote_id/v1/CONTRACT.md`
  - Format: `{interaction_id}:ch_{chunk_index}:{start_pos}-{end_pos}`
  - Status: Active, stable

- **models/chunking@v1** - Text chunking strategy (Active)
  - Purpose: Text chunking rules and tokenization strategy
  - Documentation: `.kiro/contracts/models/chunking/v1/CONTRACT.md`
  - Tokenizer: tiktoken cl100k_base (OpenAI GPT-4)
  - Status: Active, stable

## Deprecation Calendar

| Contract | Version | Announced | Last-Ship | Removal | Successor |
|----------|---------|-----------|-----------|---------|-----------|
| (none yet) | - | - | - | - | - |

### Deprecation Process

1. **Announce**: Document new version and breaking changes
   - Set last-ship date (minimum 30 days from announcement)
   - Set removal date (minimum 30 days after last-ship)
   - Communicate via team channels and update this file

2. **Last-Ship**: After this date, no new code should depend on deprecated version
   - Mark deprecated version in documentation
   - Add deprecation warnings to code
   - Provide migration guide to successor version

3. **Removal**: Version is removed from active support
   - Consumers must migrate before this date
   - Remove deprecated code and documentation
   - Update this calendar to reflect removal

## Compatibility Policy

### Semantic Versioning

Use MAJOR.MINOR.PATCH format:
- **MAJOR**: Breaking changes (requires consumer updates)
- **MINOR**: Backward-compatible additions (optional consumer updates)
- **PATCH**: Bug fixes, clarifications (no consumer changes needed)

### Version Support

- Keep 2 active MAJOR versions live during transition periods
- Support previous MAJOR version for minimum 60 days after new MAJOR release
- Provide clear migration path from old to new MAJOR version

### Breaking Changes

Breaking changes require MAJOR version bump and include:
- Removing fields from schemas
- Changing field types or semantics
- Renaming fields or endpoints
- Changing required/optional status of fields
- Modifying error codes or response structures

### Backward-Compatible Changes

Backward-compatible changes use MINOR version bump and include:
- Adding new optional fields
- Adding new endpoints or operations
- Expanding enum values
- Adding new error codes (without removing old ones)

## Communication

### Announcement Channels

All deprecations and breaking changes must be announced via:
- This file (`.kiro/steering/multi-agent-protocols.md`)
- Team Slack channel (#thematic-lm-dev)
- Engineering meeting notes
- Release notes in version control

### Migration Guides

For each MAJOR version change, provide:
- Summary of breaking changes
- Step-by-step migration instructions
- Code examples showing before/after
- Timeline for deprecation and removal
- Contact for questions or support

## Contract Categories

### API Contracts
- BFF endpoints (OpenAPI spec)
- Request/response schemas
- Error envelopes
- Authentication/authorization

### Agent Contracts
- Coder agent input/output
- Aggregator agent input/output
- Reviewer agent input/output
- Theme agent input/output

### State Contracts
- LangGraph pipeline state (TypedDict schemas)
- Checkpoint serialization format
- Database models (SQLAlchemy)

### External Contracts
- LLM provider APIs (OpenAI, Anthropic)
- Vector storage (Pinecone)
- Database (Neon Postgres)
