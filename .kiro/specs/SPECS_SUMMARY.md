# Thematic-LM Component Specifications Summary

This document provides an overview of all component specifications in the Thematic-LM system.

## Specifications Overview

### 1. orchestrator
- **spec_id**: `orchestrator`
- **Status**: Draft
- **Provides**: `internal/orchestration-pipeline@v1`
- **Consumes**: `models/chunking@v1`, `models/quote_id@v1`, `models/codebook@v1`, `models/themes@v1`
- **Key Dependencies**: All agent components, cost-manager, observability
- **Description**: LangGraph pipeline coordinator that manages job lifecycle, state transitions, and agent coordination

### 2. coder-agents
- **spec_id**: `coder-agents`
- **Status**: Draft
- **Provides**: `internal/agents-coder@v1`
- **Consumes**: `models/chunking@v1`, `models/quote_id@v1`
- **Key Dependencies**: cost-manager, OpenAI API
- **Description**: Multiple identity-based coder agents that generate codes with quotes from interactions

### 3. code-aggregator
- **spec_id**: `code-aggregator`
- **Status**: Draft
- **Provides**: `internal/agents-code-aggregator@v1`
- **Consumes**: `internal/agents-coder@v1` outputs
- **Key Dependencies**: None
- **Description**: Deduplicates and merges codes from multiple coder agents while preserving quotes

### 4. reviewer
- **spec_id**: `reviewer`
- **Status**: Draft
- **Provides**: `models/codebook@v1`
- **Consumes**: `internal/agents-code-aggregator@v1` outputs, `models/quote_id@v1`
- **Key Dependencies**: OpenAI API (embeddings), Pinecone, cost-manager
- **Description**: Updates codebook with new codes using embeddings and similarity search

### 5. theme-coder-agents
- **spec_id**: `theme-coder-agents`
- **Status**: Draft
- **Provides**: `internal/agents-theme-coder@v1`
- **Consumes**: `models/codebook@v1`
- **Key Dependencies**: cost-manager, OpenAI API, LLMLingua (compression)
- **Description**: Generates theme proposals from codebook with automatic compression for large codebooks

### 6. theme-aggregator
- **spec_id**: `theme-aggregator`
- **Status**: Draft
- **Provides**: `models/themes@v1`
- **Consumes**: `internal/agents-theme-coder@v1` outputs, `models/quote_id@v1`
- **Key Dependencies**: None
- **Description**: Merges and curates final themes with quality thresholds

### 7. bff-api
- **spec_id**: `bff-api`
- **Status**: Draft
- **Provides**: `apis/bff@v1`
- **Emits**: `events/analysis-events@v1`
- **Consumes**: `internal/orchestration-pipeline@v1`
- **Key Dependencies**: cost-manager, tenancy-security, observability
- **Description**: FastAPI service layer with authentication, cost guards, and 202+polling semantics

### 8. observability
- **spec_id**: `observability`
- **Status**: Draft
- **Provides**: `observability/logging@v1`, `observability/health@v1`
- **Consumes**: None
- **Key Dependencies**: None
- **Description**: Health endpoints, structured logging, and checkpoint cleanup job

### 9. cost-manager
- **spec_id**: `cost-manager`
- **Status**: Draft
- **Provides**: `internal/cost-management@v1`
- **Consumes**: None
- **Key Dependencies**: None
- **Description**: Budget estimation, enforcement, rate limiting, and retry logic

### 10. tenancy-security
- **spec_id**: `tenancy-security`
- **Status**: Draft
- **Provides**: `internal/security-rls@v1`, `internal/security-auth@v1`
- **Consumes**: None
- **Key Dependencies**: Neon Postgres
- **Description**: RLS enforcement, database roles, auth middleware, and audit logging

## Contract Dependencies Matrix

| Component | Provides | Consumes | Emits |
|-----------|----------|----------|-------|
| orchestrator | internal/orchestration-pipeline@v1 | chunking@v1, quote_id@v1, codebook@v1, themes@v1 | - |
| coder-agents | internal/agents-coder@v1 | chunking@v1, quote_id@v1 | - |
| code-aggregator | internal/agents-code-aggregator@v1 | internal/agents-coder@v1 | - |
| reviewer | codebook@v1 | internal/agents-code-aggregator@v1, quote_id@v1 | - |
| theme-coder-agents | internal/agents-theme-coder@v1 | codebook@v1 | - |
| theme-aggregator | themes@v1 | internal/agents-theme-coder@v1, quote_id@v1 | - |
| bff-api | apis/bff@v1 | internal/orchestration-pipeline@v1 | events/analysis-events@v1 |
| observability | observability/logging@v1, observability/health@v1 | - | - |
| cost-manager | internal/cost-management@v1 | - | - |
| tenancy-security | internal/security-rls@v1, internal/security-auth@v1 | - | - |

## Implementation Order

Recommended implementation order based on dependencies:

1. **Phase 1: Foundation**
   - cost-manager (no dependencies)
   - observability (no dependencies)
   - tenancy-security (no dependencies)

2. **Phase 2: Agents**
   - coder-agents (depends on cost-manager)
   - code-aggregator (depends on coder-agents)
   - reviewer (depends on code-aggregator, cost-manager)

3. **Phase 3: Theme Generation**
   - theme-coder-agents (depends on reviewer output, cost-manager)
   - theme-aggregator (depends on theme-coder-agents)

4. **Phase 4: Orchestration**
   - orchestrator (depends on all agents)

5. **Phase 5: API**
   - bff-api (depends on orchestrator, cost-manager, tenancy-security, observability)

## Testing Strategy

### Unit Tests
- All components: Pure logic with mocks
- No external dependencies
- Fast execution (<1s per test)

### Integration Tests
- Gated by `LIVE_TESTS=1`
- Test with real APIs (OpenAI, Pinecone, Neon)
- Respect `COST_BUDGET_USD`
- Components: coder-agents, reviewer, theme-coder-agents, orchestrator

### E2E Tests
- Full pipeline with small dataset (5-10 interactions)
- Gated by `LIVE_TESTS=1`
- Validates entire workflow
- Component: orchestrator (with all dependencies)

## Configuration Files

- `identities.yaml`: Coder identity perspectives (loaded at process start)
- `.env`: Environment variables (DATABASE_URL, OPENAI_API_KEY, etc.)
- `.kiro/settings/mcp.json`: MCP server configuration

## Next Steps

1. ✅ All specs created with requirements, design, tasks, and dependencies
2. ⏭️ Begin implementation with Phase 1 (foundation components)
3. ⏭️ Set up CI pipeline with contract validation
4. ⏭️ Implement unit tests for each component
5. ⏭️ Implement integration tests (gated by LIVE_TESTS=1)
6. ⏭️ Implement E2E smoke test
7. ⏭️ Deploy to staging environment
8. ⏭️ Conduct user acceptance testing
9. ⏭️ Deploy to production

## Status Legend

- **Draft**: Specification in progress, not yet approved
- **Approved**: Specification reviewed and approved for implementation
- **In Progress**: Implementation underway
- **Shipped**: Component deployed to production
- **Deprecated**: Component no longer in active use
