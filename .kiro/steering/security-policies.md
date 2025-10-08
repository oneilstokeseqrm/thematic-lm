# Security Policies

## Row-Level Security (RLS)

### Enforcement
- Enabled on all tenant/account-scoped tables
- Enforced via session variable `app.current_account_id`
- Policy example:
  ```sql
  CREATE POLICY tenant_isolation ON codes
    FOR SELECT USING (account_id = current_setting('app.current_account_id')::uuid);
  ```

### Tenant-Scoped Tables
- `interactions`: Raw text data
- `codes`: Generated codes with quotes
- `themes`: Final themes
- `analysis_jobs`: Job metadata
- `analysis_checkpoints`: Pipeline state
- `codebook_versions`: Codebook snapshots

## Database Roles and Privileges

### Least Privilege Model

#### `app_user` Role
- **Purpose**: All user-facing queries
- **Privileges**: RLS enabled on all multi-tenant tables
- **Restrictions**: No BYPASSRLS; no superuser privileges
- **Usage**: Set `app.current_account_id` at session start based on auth token

#### `db_service` Role
- **Purpose**: Internal pipeline operations only
- **Privileges**: BYPASSRLS for checkpointing and admin queries
- **Restrictions**: Never used in user-facing API operations
- **Usage**: Checkpoint writes, cross-tenant analytics (tightly controlled)

#### `migrations` Role
- **Purpose**: Schema modification only
- **Privileges**: DDL operations (CREATE, ALTER, DROP)
- **Restrictions**: No data access (no SELECT, INSERT, UPDATE, DELETE)
- **Usage**: Alembic migrations only

## Secrets Management

### Never Commit Secrets
- All secrets excluded via `.gitignore`
- Use `.env.example` as template (no actual values)
- Review commits for accidental secret exposure

### Local Development
- Store secrets in `.env` file (gitignored)
- Load via Pydantic settings in `config.py`
- Validate required secrets on startup; fail fast if missing

### CI/CD
- Use secure environment variables or secret manager
- Never log secrets (even at DEBUG level)
- Rotate secrets regularly (quarterly minimum)

## PII Handling (v1 Scope)

### No PII Redaction Module in v1
- Assume input data is public or clients have consent
- Flag for future enhancement: optional per-tenant PII redaction toggle

### Logging Redaction Rules
- **Never log raw interaction text at INFO level**
- Use DEBUG level with explicit opt-in for content logging
- Scrub PII patterns from logs (emails, phone numbers, SSNs)
- Log only metadata at INFO: `interaction_id`, `chunk_count`, `code_count`

### Future Enhancement
- PII detection module (regex + NER) for preprocessing
- Anonymize data before LLM API calls
- Map results back to original identifiers if needed

## LLM API Privacy

### Data Privacy Modes
- Use OpenAI's opt-out for data logging/sharing
- Ensure API calls don't log sensitive content beyond processing needs
- Review provider compliance and privacy policies

### On-Premise Options
- Support self-hosted models for stricter data control
- Route requests to different models based on tenant requirements
- Document trade-offs (cost, performance, privacy)

## Authentication & Authorization

### API Authentication
- Require valid JWT tokens or API keys for all requests
- Token encodes tenant/account context
- Invalid/missing token returns 401 Unauthorized

### Authorization Checks
- Verify token scopes (user may only access authorized accounts)
- Set `app.current_account_id` from token for RLS enforcement
- Rate limit per user to prevent abuse

### Token Management
- Short-lived access tokens (15 minutes)
- Refresh tokens for extended sessions
- Revoke tokens on logout or security events

## Audit Logging (v1 Minimal)

### Required Audit Fields
All tables with sensitive data must include:
- `tenant_id`: Tenant identifier
- `account_id`: Account identifier
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### API Operation Logging
All API operations must log:
- `analysis_id`: Job identifier
- `trace_id`: Request correlation ID
- `user_id`: Authenticated user (if available)
- `action`: Operation performed (e.g., "create_analysis", "get_results")
- `status`: Success or failure
- `timestamp`: Operation timestamp

### Deferred to Post-v1
- Expanded audit fields: `created_by`, `updated_by`, `correlation_id`
- Audit trail for all data access (SELECT queries)
- Compliance reporting (GDPR, HIPAA)
