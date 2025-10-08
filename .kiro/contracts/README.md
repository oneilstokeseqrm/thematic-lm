# Thematic-LM Contracts

This directory contains machine-readable schemas and human documentation for all contracts in the Thematic-LM system. Contracts define the interfaces between agents, pipeline stages, and external systems.

## Purpose

Contracts serve multiple purposes:
- **Interface Definition**: Clear specifications for data structures and APIs
- **Validation**: Machine-readable schemas enable automated validation
- **Documentation**: Human-readable docs explain intent and usage
- **Versioning**: Track changes and manage deprecations
- **Testing**: Examples provide test fixtures and validation targets

## Organization

```
.kiro/contracts/
├── events/              # Event schemas for pipeline lifecycle
│   └── analysis-events/
│       └── v1/
│           ├── schema.json      # JSON Schema
│           ├── CONTRACT.md      # Human documentation
│           └── examples/        # Example events
├── apis/                # API specifications
│   └── bff/
│       └── v1/
│           ├── openapi.yaml     # OpenAPI 3.0 spec
│           └── examples/        # Request/response examples
└── models/              # Data model contracts
    ├── codebook/
    │   └── v1/
    │       ├── schema.json
    │       ├── CONTRACT.md
    │       └── examples/
    ├── themes/
    │   └── v1/
    │       ├── schema.json
    │       ├── CONTRACT.md
    │       └── examples/
    ├── quote_id/
    │   └── v1/
    │       ├── CONTRACT.md      # Format specification
    │       └── examples/        # Quote ID examples
    └── chunking/
        └── v1/
            ├── CONTRACT.md      # Chunking strategy
            └── examples/        # Chunking examples
```

## Contract Types

### Events Contracts
Define event schemas for the analysis pipeline lifecycle. Events enable event-driven architectures and real-time notifications.

**Location**: `events/`

**Current Contracts**:
- `analysis-events@v1`: Analysis lifecycle events (accepted, completed, failed)

### API Contracts
Define REST API specifications using OpenAPI 3.0. Include request/response schemas, error envelopes, and authentication.

**Location**: `apis/`

**Current Contracts**:
- `bff@v1`: Backend-For-Frontend API for analysis submission and status polling

### Model Contracts
Define data structures for codebooks, themes, quotes, and other domain models.

**Location**: `models/`

**Current Contracts**:
- `codebook@v1`: Adaptive codebook structure with codes and quotes
- `themes@v1`: Theme output format with supporting quotes and code references
- `quote_id@v1`: Quote ID encoding format and validation rules
- `chunking@v1`: Text chunking strategy and tokenization rules

## Adding New Contracts

### 1. Create Directory Structure

```bash
mkdir -p .kiro/contracts/{category}/{contract_name}/v1/examples
```

### 2. Create Schema (if applicable)

For JSON-based contracts, create `schema.json`:
- Include `$schema: "http://json-schema.org/draft-07/schema#"`
- Include `$id` with unique URI
- Set `additionalProperties: false` on all objects
- Use `format: uuid` for all ID fields
- Use `format: date-time` for all timestamp fields
- Use enums for fields with fixed value sets

### 3. Create Documentation

Create `CONTRACT.md` with:
- **Purpose**: What this contract defines
- **Usage**: When and how to use it
- **Validation Rules**: What makes a valid instance
- **Versioning**: Breaking vs non-breaking changes
- **Examples**: Link to examples directory

### 4. Create Examples

Add at least 2-3 examples in `examples/`:
- Valid examples that pass schema validation
- Cover common use cases
- Include edge cases if relevant
- Use realistic data (not "foo", "bar")

### 5. Update multi-agent-protocols.md

Add contract to "Active Contracts" section:
```markdown
- {category}/{contract_name}@v1 - {description} (Active)
```

### 6. Run Validation

```bash
python scripts/validate_contracts.py
```

## Validation

All contracts are validated automatically:

### Local Validation
```bash
# Validate all contracts
python scripts/validate_contracts.py

# Validate specific contract
python scripts/validate_contracts.py --contract events/analysis-events/v1
```

### CI Validation
Contract validation runs in CI on every commit. Validation failures block merges.

### What is Validated
1. **Schema Validity**: All JSON schemas are valid against JSON Schema meta-schema (draft-07)
2. **Example Validity**: All examples validate against their corresponding schemas
3. **Quote ID Format**: All quote IDs match canonical regex pattern
4. **UUID Format**: All UUIDs are valid format
5. **Timestamp Format**: All timestamps are valid ISO 8601
6. **Required Fields**: All required fields are present in schemas

## Versioning

### Semantic Versioning

Contracts use semantic versioning: `v{MAJOR}`

- **MAJOR**: Breaking changes (requires consumer updates)
  - Removing required fields
  - Changing field types
  - Renaming fields
  - Changing validation rules (stricter)

### Version Support

- Keep 2 active MAJOR versions live during transition periods
- Support previous MAJOR version for minimum 60 days after new MAJOR release
- Provide clear migration path from old to new MAJOR version

### Deprecation Process

1. **Announce**: Document new version and breaking changes
   - Set last-ship date (minimum 30 days from announcement)
   - Set removal date (minimum 30 days after last-ship)
   - Update `multi-agent-protocols.md` deprecation calendar

2. **Last-Ship**: After this date, no new code should depend on deprecated version
   - Mark deprecated version in documentation
   - Add deprecation warnings to code

3. **Removal**: Version is removed from active support
   - Consumers must migrate before this date
   - Remove deprecated schemas and documentation
   - Update deprecation calendar

## JSON Schema Standards

All JSON schemas must follow these standards:

### Required Fields
- `$schema`: `"http://json-schema.org/draft-07/schema#"`
- `$id`: Unique URI (e.g., `"https://thematic-lm.eq.com/schemas/{path}/schema.json"`)
- `title`: Human-readable title
- `description`: Brief description of the schema

### Object Properties
- Set `additionalProperties: false` on all objects to prevent drift
- Use `required` array to specify required fields
- Provide `description` for all fields

### Field Formats
- **UUIDs**: `"type": "string", "format": "uuid"`
- **Timestamps**: `"type": "string", "format": "date-time"` (ISO 8601)
- **Dates**: `"type": "string", "format": "date"` (ISO 8601)
- **Enums**: Use `"enum": [...]` for fixed value sets

### Validation Rules
- Use `minimum`, `maximum` for numeric bounds
- Use `minLength`, `maxLength` for string bounds
- Use `minItems`, `maxItems` for array bounds
- Use `pattern` for regex validation

## Testing

### Contract Tests

Contract tests validate that implementations match specifications:

```python
# tests/contract/test_analysis_events.py
import json
import jsonschema

def test_analysis_accepted_event_validates():
    with open('.kiro/contracts/events/analysis-events/v1/schema.json') as f:
        schema = json.load(f)
    
    with open('.kiro/contracts/events/analysis-events/v1/examples/analysis_accepted.json') as f:
        example = json.load(f)
    
    # Should not raise
    jsonschema.validate(example, schema)
```

### Example Validation

All examples are validated against their schemas in CI:

```bash
python scripts/validate_contracts.py
```

## References

- [JSON Schema Draft-07](https://json-schema.org/draft-07/json-schema-release-notes.html)
- [OpenAPI 3.0 Specification](https://swagger.io/specification/)
- [ISO 8601 Date/Time Format](https://en.wikipedia.org/wiki/ISO_8601)
- [UUID Format (RFC 4122)](https://tools.ietf.org/html/rfc4122)
