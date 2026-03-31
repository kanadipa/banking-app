# Banking API

Internal banking API built with FastAPI, PostgreSQL, and SQLAlchemy 2.0 async.

## Features

- **Customers**: list (paginated), get by ID with accounts
- **Accounts**: create with initial deposit (EUR), check balance
- **Transfers**: between accounts, idempotent via `reference`, balance snapshots
- **Transfer history**: paginated, shows direction + counterparty + balance after each transfer
- **`X-Requested-By` header**: tracks who made each request (audit trail)
- **Concurrency safe**: row-level locks prevent double-spend
- **Money**: `NUMERIC(12,2)` in Postgres, `Decimal` in Python — never floats

## Prerequisites

[Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

## Getting started

```bash
cd banking-api-rdxvmq

# Create your local .env from the template
cp .env.example .env

# Start everything
docker compose up --build
```

Wait for `Uvicorn running on http://localhost:8000`, then open:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check**: [http://localhost:8000/health](http://localhost:8000/health)

To stop:

```bash
docker compose down -v
```

## Seeded customers

4 customers are created on startup:

| ID | Name            |
|----|-----------------|
| 1  | Arisha Barron   |
| 2  | Branden Gibson  |
| 3  | Rhonda Church   |
| 4  | Georgina Hazel  |

## Authentication

Every endpoint (except `/health`) requires two headers:

| Header           | Description                          | Example              |
|------------------|--------------------------------------|----------------------|
| `X-API-Key`      | API key (placeholder for OAuth/JWT)  | `dev-internal-key`   |
| `X-Requested-By` | Who is making the request            | `employee:jane.doe`  |

## API endpoints

### `GET /customers?page=1&max_size=20`

List customers (paginated).

```bash
curl -H 'X-API-Key: dev-internal-key' -H 'X-Requested-By: jane' \
  'http://localhost:8000/customers?page=1&max_size=10'
```

### `GET /customers/{id}`

Customer detail with their accounts.

```bash
curl -H 'X-API-Key: dev-internal-key' -H 'X-Requested-By: jane' \
  http://localhost:8000/customers/1
```

### `POST /customers/{id}/accounts`

Create an account with an initial deposit.

```bash
curl -X POST http://localhost:8000/customers/1/accounts \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-internal-key' \
  -H 'X-Requested-By: jane' \
  -d '{"initial_deposit": "1000.00"}'
```

### `GET /accounts/{id}/balance`

```bash
curl -H 'X-API-Key: dev-internal-key' -H 'X-Requested-By: jane' \
  http://localhost:8000/accounts/1/balance
```

### `POST /transfers`

Transfer money. `reference` is an idempotency key — same reference = same transfer returned.

```bash
curl -X POST http://localhost:8000/transfers \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-internal-key' \
  -H 'X-Requested-By: jane' \
  -d '{"from_account_id": 1, "to_account_id": 2, "amount": "25.50", "reference": "rent-march"}'
```

### `GET /accounts/{id}/transfers?page=1&max_size=20`

Transfer history with direction, counterparty info, and balance after each transaction.

```bash
curl -H 'X-API-Key: dev-internal-key' -H 'X-Requested-By: jane' \
  'http://localhost:8000/accounts/1/transfers?page=1&max_size=10'
```

### `GET /health`

No auth required.

## Running tests

Tests use `.env.test` (committed to the repo — safe, only local Docker credentials).

```bash
docker compose run --rm app pytest -q
```

## Linting

```bash
docker compose run --rm app ruff check .
```

## Error responses

| Status | Error key                | When                                  |
|--------|--------------------------|---------------------------------------|
| 400    | `bad_request`            | Missing required header               |
| 401    | `unauthorized`           | Invalid or missing API key            |
| 404    | `not_found`              | Customer or account doesn't exist     |
| 409    | `insufficient_funds`     | Not enough balance for transfer       |
| 422    | `validation_error`       | Invalid request body (with `errors[]`)|
| 422    | `business_rule_violation`| e.g. self-transfer                    |
| 500    | `server_error`           | Unexpected database or server error   |

## Environment & secrets

| File           | Committed? | Purpose                                      |
|----------------|------------|----------------------------------------------|
| `.env.example` | Yes        | Template — `cp .env.example .env` to start   |
| `.env`         | **No**     | Your local secrets (in `.gitignore`)         |
| `.env.test`    | Yes        | Test config (safe, local Docker only)        |

In production, use a secrets manager (AWS Secrets Manager, Vault, etc.) instead of `.env` files.

## CI

GitHub Actions pipeline in `.github/workflows/ci.yml` — runs `ruff check` + `pytest` against a Postgres service container on every push/PR to `main`.

**Setup required:** add these repository secrets in GitHub → Settings → Secrets and variables → Actions:

| Secret                | Example value  |
|-----------------------|----------------|
| `POSTGRES_DB_CI`      | `banking`      |
| `POSTGRES_USER_CI`    | `banking`      |
| `POSTGRES_PASSWORD_CI`| (TBD)          |
| `POSTGRES_HOST_CI`    | `localhost`    |
| `API_KEY_CI`          | `test-key`     |

No credentials are hardcoded in the workflow file.

## Architecture

```
api/routes/     → HTTP endpoints (thin, delegate to service)
services/       → Business logic (validation, transfers, idempotency)
repositories/   → Database queries (SELECT, INSERT, locking)
models/         → SQLAlchemy ORM (Customer, Account, Transfer)
schemas/        → Pydantic request/response models
scripts/        → init_db, seed_customers
core/           → Config (.env), auth, logging
```

## Road to production

See [`docs/production-readiness.md`](docs/production-readiness.md) — covers OAuth/JWT, PSD2 identity verification (photoTAN, SantanderSign), full account schema (DOB, address, credit score, income), KYC/AML, audit logging, multi-currency with FX rates, rate limiting, observability, GDPR, and CI/CD.
