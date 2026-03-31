# Production Readiness

This document outlines what would be needed before deploying this API to a real banking environment. The current implementation is a working prototype only.

## Authentication & Authorization

- Replace `X-API-Key` with OAuth2 / OpenID Connect (e.g. Keycloak, Auth0)
- Replace `X-Requested-By` header with claims extracted from JWT tokens
- Add role-based access control: teller, manager, auditor, admin
- Scope permissions per endpoint (e.g. only managers can create accounts)

## Identity Verification for Transfers

In a German banking context, transfers above certain thresholds require strong customer authentication (SCA) under PSD2:

- **Integration pattern**: Before executing a transfer, the API would call an external SCA provider, receive a challenge token, wait for customer approval, then proceed. This would add a `pending_approval` transfer status and a webhook/polling flow for confirmation.
- **Threshold rules**: Transfers under a configurable limit (e.g. €30) may be exempt from SCA per PSD2 exemptions

## Full Account Object (Production Schema)

The current `Account` model is intentionally minimal. A production account would include:

```
Account
├── id (UUID)
├── customer_id
├── account_holder_name
├── date_of_birth
├── address
│   ├── street
│   ├── city
│   ├── postal_code
│   ├── country
│   └── address_type (residential / business / mailing)
├── credit_score
├── annual_income
├── balance
├── currency
├── status (active / frozen / closed)
├── initial_deposit_amount
├── initial_deposit_method (bank_transfer / cash / card)
├── initial_deposit_source (salary / savings / gift / other)
├── linked_account_ids[] (other accounts held by same customer)
├── created_by (employee ID who opened the account)
├── created_at
├── updated_at
└── closed_at
```

Each transfer would also expand:

```
Transfer
├── id (UUID)
├── transaction_type (internal / SEPA / instant)
├── sca_method (photoTAN / pushTAN / exempt)
├── sca_approved_at
├── requested_by (employee or customer ID)
├── approved_by (for dual-control scenarios)
└── ...existing fields
```

## KYC / AML Compliance

- Know Your Customer (KYC) verification before account opening
- Anti-Money Laundering (AML) screening on every transfer (sanctions lists, PEP checks)
- Integration with providers like Onfido, IDnow, or Schufa (Germany)
- Automated suspicious activity reporting (SAR)

## Audit Logging

- Immutable audit trail for every state change (account created, balance changed, transfer executed)
- Store: who did it, when, what changed, from which IP
- Use an append-only audit table or ship to an external system (e.g. Elasticsearch, Splunk)

## Multi-Currency Support

Currently the API uses EUR only. Production would need:

- Currency field on account creation
- Exchange rate service integration (e.g. ECB rates, Wise API)
- FX conversion logic with transparent rate display
- Validation that cross-currency transfers include exchange rate consent

## Secrets Management

- Use a secrets manager in production: AWS Secrets Manager, HashiCorp Vault, or GCP Secret Manager
- Rotate database credentials periodically
- API keys should be hashed, not stored in plaintext

## Rate Limiting & Abuse Prevention

- Rate limit per API key / IP (e.g. 100 requests/minute)
- Stricter limits on write endpoints (transfers, account creation)
- Consider Redis-backed rate limiting (e.g. `slowapi` or a gateway like Kong)

## Observability

- Structured JSON logging (replace current text format)
- Request tracing with correlation IDs (OpenTelemetry)
- Metrics: request latency, error rates, transfer volumes (Prometheus + Grafana)
- Alerting on error spikes, failed transfers, unusual transfer patterns

## Database Hardening

- Connection pooling (PgBouncer in production)
- Read replicas for GET endpoints
- Point-in-time recovery and automated backups
- Database migrations via Alembic (removed from this exercise for simplicity, but essential in production)
- Zero-downtime migration strategy

## CI/CD

- The included GitHub Actions pipeline (`ci.yml`) runs tests on every push
- Production pipeline would add: linting, type checking (mypy), security scanning (Bandit), Docker image building, and deployment to staging → production

## API Versioning

- Prefix all routes with `/v1/` once external clients depend on the contract
- Maintain backward compatibility or provide deprecation windows

## Data Protection (GDPR)

- Encrypt PII at rest and in transit
- Implement data retention policies
- Support right-to-erasure requests
- Log access to personal data for compliance audits
