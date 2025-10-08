# Analysis Events Contract v1

## Purpose

Analysis events provide real-time notifications about the lifecycle of analysis jobs. These events enable event-driven architectures where consumers can react to analysis state changes without polling.

## Event Types

### analysis_accepted

**When Emitted**: Immediately after POST /analyze returns 202 Accepted

**Purpose**: Notify consumers that an analysis job has been accepted and queued for processing

**Consumer Expectations**:
- Job is queued but not yet started
- `estimated_cost_usd` is the pre-execution cost estimate
- Consumers should begin polling GET /analysis/{analysis_id} or wait for completion event
- Event is emitted synchronously before API response returns

### analysis_completed

**When Emitted**: When analysis finishes successfully after theme generation stage

**Purpose**: Notify consumers that results are available

**Consumer Expectations**:
- Full results are available via GET /analysis/{analysis_id}
- `results.themes` contains summary (full themes in API response)
- `codebook_version` can be used to retrieve the codebook snapshot
- Event is emitted asynchronously after pipeline completion

### analysis_failed

**When Emitted**: When analysis fails at any stage (coding, theme generation, or infrastructure failure)

**Purpose**: Notify consumers of failure with error details

**Consumer Expectations**:
- Analysis will not complete; no results available
- `error.code` indicates failure reason (see api-standards.md for error codes)
- `error.detail` may contain actionable guidance
- Consumers should not retry automatically; user intervention may be required
- Event is emitted asynchronously when failure is detected

## Event Delivery

### Transport (v1)
- Events are written to database `analysis_events` table
- Consumers poll table or use database triggers (event streaming deferred to post-v1)

### Future (Post-v1)
- Redis Streams or Kafka for real-time event delivery
- Consumer groups per tenant for isolation
- Event retention: 7 days

## Versioning Rules

### Breaking Changes (Require v2)
- Removing required fields
- Changing field types
- Renaming fields
- Changing event_type enum values

### Non-Breaking Changes (Allowed in v1)
- Adding optional fields
- Adding new event types
- Expanding nested object properties (if additionalProperties: true)

### Deprecation Process
- Announce 60 days before removal
- Support v1 and v2 in parallel for 60 days
- Document migration path in multi-agent-protocols.md

## Schema Validation

All events must validate against `schema.json` before emission. Validation failures should:
1. Log error with full event payload
2. Increment validation_error metric
3. Not block pipeline execution (fail open)
4. Alert engineering team if error rate > 1%
