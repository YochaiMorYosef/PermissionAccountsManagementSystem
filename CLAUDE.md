# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A multi-tenant serverless permissions management REST API built with Python 3.13 on AWS Lambda, DynamoDB, and SQS, deployed via Serverless Framework v3.

## Setup

```bash
npm install        # Serverless Framework plugins
poetry install     # Python runtime + dev dependencies
```

**Prerequisites:** Node.js 18+, Python 3.13, Poetry 1.8+, Serverless Framework v3

## Commands

```bash
# Run all tests
poetry run pytest

# Run a single test file
poetry run pytest tests/unit/test_time_filtering.py -v

# Deploy
npx serverless deploy
npx serverless deploy --stage prod

# Load bulk data into DynamoDB
python script/load_data.py --table permissions-dev --region us-east-1 --workers 10
```

## Architecture

**Three-layer architecture:**
- `src/handlers/` — Lambda entry points (7 endpoints); parse JWT, call BL, return response
- `src/bl/` — Business logic; orchestrates validation, repo calls, SQS dispatch
- `src/repositories/` — DynamoDB access (single table: `permissions-{stage}`, PK=`tenant_id`, SK=`permission_id`)

**Async provisioning flow:** Create/delete operations write to DynamoDB with a transitional status (`Creating`/`Deleting`), then enqueue an SQS message to `permissions-queue-{stage}`. The worker Lambda (`processPermission`) calls an external provisioning URL and updates status in DynamoDB.

**JWT auth:** Bearer tokens are decoded without signature verification (intentional for this exercise). `tenant_id` is extracted for multi-tenant isolation; optional `sub` claim identifies the calling user.

**Schedule entries:** Optional time windows (weekday + HH:MM start/end, UTC) control when permissions are active. Overnight windows (start > end) are supported.

## Key Utilities

- `src/utils/jwt_parser.py` — JWT decode (no sig verification), extracts `tenant_id` and `sub`
- `src/utils/validation.py` — Input validation for create/update, schedule time format (HH:MM, 00:00–23:59)
- `src/utils/response.py` — Standardized API responses with CORS headers (all origins)
- `src/utils/logger.py` — JSON-structured logging for CloudWatch with `request_id` / `tenant_id` context

## Environment Variables

Set automatically by Serverless Framework; needed locally for integration tests:

| Variable | Description |
|---|---|
| `TABLE_NAME` | DynamoDB table name |
| `QUEUE_URL` | SQS queue URL |
| `PROVISIONING_URL` | External provisioning endpoint |
| `DEMO_AUTH_TOKEN` | Static token for provisioning calls |
| `LOG_LEVEL` | Logging level (default: INFO) |

## Testing

- `tests/unit/` — Pure unit tests with mocks
- `tests/integration/` — Handler-level tests using `moto` (mocked DynamoDB + SQS)
- `tests/e2e/` — End-to-end tests
- `conftest.py` at root configures `PYTHONPATH` for test discovery

## Known Behaviors

- A bug exists where `GET /permissions/me` returns empty results — described in `exercise.md` task 4
- JWT signatures are intentionally not validated in this exercise
- DynamoDB table has no secondary indexes; queries filter by `tenant_id` partition key only
