# Permissions Service

A serverless REST API for managing user permissions, built with the Serverless Framework, AWS Lambda (Python 3.13), DynamoDB, and SQS.

## Overview

This service allows you to grant, manage, and query permissions for users on specific accounts. A permission can optionally be scoped to time windows (e.g., "only on Mondays from 09:00–17:00 UTC"). If no schedule is provided, the permission is always active.

All API endpoints require a JWT Bearer token. The `tenant_id` is always resolved from the token and never passed directly by the client, ensuring strict tenant isolation.

Create and delete operations are asynchronous — the API writes to DynamoDB with a transitional `status`, then dispatches an SQS message to a worker Lambda that calls a configurable provisioning URL.

## Architecture

```
Client
  │
  │  Authorization: Bearer <JWT>
  ▼
API Gateway (REST)
  │
  ├── POST   /permissions              → createPermission Lambda
  ├── GET    /permissions              → queryPermissions Lambda
  ├── GET    /permissions/me           → getUserPermissions Lambda
  ├── GET    /permissions/{id}         → getPermission Lambda
  ├── PATCH  /permissions/{id}         → updatePermission Lambda
  └── DELETE /permissions/{id}         → deletePermission Lambda
                      │                        │
                      ▼                        ▼
               DynamoDB: permissions-{stage}
               PK: tenant_id | SK: permission_id
                      │
                      ▼ (SQS message on create / delete)
               PermissionsQueue (SQS)
                      │
                      ▼
               processPermission Lambda
                      │
                      ▼
               External provisioning URL (HTTP POST)
```

## Data Model

### Permission

| Field           | Type                  | Description                                              |
|-----------------|-----------------------|----------------------------------------------------------|
| `tenant_id`     | String (PK)           | Tenant identifier — always resolved from JWT             |
| `permission_id` | String (SK)           | Auto-generated UUID                                      |
| `user`          | String                | User identifier the permission is granted to             |
| `account_id`    | String                | The account/resource this permission applies to          |
| `permission`    | String                | The permission type or action being granted              |
| `status`        | String (enum)         | Lifecycle status (see below)                             |
| `schedule`      | List\<ScheduleEntry\> \| null | Active time windows. `null` means always active |

### Permission Status

| Value            | Meaning                                                        |
|------------------|----------------------------------------------------------------|
| `Creating`       | Written to DynamoDB; provisioning SQS message sent            |
| `Active`         | Provisioning HTTP call succeeded                               |
| `FailedCreating` | Provisioning HTTP call failed                                  |
| `Deleting`       | Delete accepted; deprovisioning SQS message sent               |
| `FailedDeleting` | Deprovisioning HTTP call failed; record still in DynamoDB      |

### ScheduleEntry

| Field        | Type    | Description                                             |
|--------------|---------|---------------------------------------------------------|
| `weekday`    | Integer | Day of the week: `0` = Monday … `6` = Sunday           |
| `start_time` | String  | `HH:MM` format, UTC                                     |
| `end_time`   | String  | `HH:MM` format, UTC. Can be earlier than `start_time` for overnight windows |

## API Reference

All responses follow this envelope:

- **Success**: `{ "data": <payload> }`
- **Error**: `{ "error": { "message": "<description>" } }`

### POST `/permissions`

Create a new permission. Returns `201` with the created permission at `status: Creating`. An SQS message is dispatched; once the worker Lambda succeeds, the status becomes `Active`.

**Request body:**

```json
{
  "user": "alice",
  "account_id": "account-123",
  "permission": "read",
  "schedule": [
    { "weekday": 0, "start_time": "09:00", "end_time": "17:00" }
  ]
}
```

Omit `schedule` or set it to `null` for an always-active permission.

**Response `201`:**

```json
{
  "data": {
    "tenant_id": "tenant-abc",
    "permission_id": "550e8400-e29b-41d4-a716-446655440000",
    "user": "alice",
    "account_id": "account-123",
    "permission": "read",
    "status": "Creating",
    "schedule": [{ "weekday": 0, "start_time": "09:00", "end_time": "17:00" }]
  }
}
```

---

### GET `/permissions/{permission_id}`

Retrieve a single permission by ID.

**Response `200`:** Permission object.

**Response `404`:** Permission not found.

---

### PATCH `/permissions/{permission_id}`

Update one or more fields. Only the fields included in the body are changed.

**Request body (any subset of updatable fields):**

```json
{ "permission": "write" }
```

To remove a schedule and make a permission always-active:

```json
{ "schedule": null }
```

**Response `200`:** Updated permission object.

---

### DELETE `/permissions/{permission_id}`

Initiates an asynchronous delete. The permission's status is set to `Deleting` and an SQS message is dispatched. The worker Lambda calls the provisioning URL; on success the record is removed from DynamoDB, on failure the status is set to `FailedDeleting`.

**Response `204`:** No content — delete accepted.

**Response `404`:** Permission not found.

---

### GET `/permissions`

Query all permissions for the caller's tenant. Optionally filter by query parameters.

**Query parameters (all optional):**

| Parameter    | Description               |
|--------------|---------------------------|
| `user`       | Filter by user            |
| `account_id` | Filter by account         |
| `permission` | Filter by permission type |

**Response `200`:** Array of permission objects.

---

### GET `/permissions/me`

Returns a deduplicated, sorted list of permission action strings the caller currently holds on a given account. The user is identified by the `sub` claim in the JWT. Only permissions with `status: Active` are included. A permission is considered time-active if its `schedule` is `null` (always active) or if any schedule entry matches the current UTC weekday and time.

**Query parameters:**

| Parameter    | Required | Description         |
|--------------|----------|---------------------|
| `account_id` | Yes      | The account to check |

**Response `200`:**

```json
{ "data": ["admin", "read", "write"] }
```

---

## Project Structure

```
exercise/
├── serverless.yml              Serverless Framework configuration
├── pyproject.toml              Poetry dependency management
├── openapi.yml                 OpenAPI 3.0 specification
├── README.md
├── script/
│   ├── generate_data.py        Generate large mock dataset → permissions.data
│   └── load_data.py            Bulk-load permissions.data into DynamoDB
└── src/
    ├── handlers/               Lambda entry points (one per endpoint)
    │   ├── create_permission.py
    │   ├── get_permission.py
    │   ├── update_permission.py
    │   ├── delete_permission.py
    │   ├── query_permissions.py
    │   ├── get_user_permissions.py
    │   └── process_permission.py   SQS consumer
    ├── bl/                     Business logic
    │   ├── create_permission.py
    │   ├── get_permission.py
    │   ├── update_permission.py
    │   ├── delete_permission.py
    │   ├── query_permissions.py
    │   ├── get_user_permissions.py
    │   ├── process_permission.py   HTTP provisioning + status update
    │   └── time_filtering.py       Schedule window evaluation
    ├── models/
    │   ├── permission.py           Permission and ScheduleEntry dataclasses
    │   ├── permission_status.py    PermissionStatus enum
    │   ├── api_models.py           Field name sets used across layers
    │   └── exceptions.py           Custom exception types
    ├── repositories/
    │   └── permissions_repo.py     DynamoDB access layer
    └── utils/
        ├── jwt_parser.py       JWT claim extraction (no signature verification)
        ├── response.py         Standardized API response builder
        ├── validation.py       Input validation helpers
        ├── sqs.py              SQS send_message wrapper
        └── logger.py           Structured JSON logger
```

## Prerequisites

- Python 3.13
- [Poetry](https://python-poetry.org/) 1.8+
- Node.js 18+
- AWS CLI configured with appropriate credentials
- Serverless Framework v3

## Setup

**Install Node.js dependencies (Serverless plugins):**

```bash
npm install
```

**Install Python dependencies (runtime + dev) via Poetry:**

```bash
poetry install
```

## Running Tests

```bash
poetry run pytest
```

Tests are split into:

- `tests/unit/` — pure unit tests using mocks (no AWS required)
- `tests/integration/` — handler-level tests with DynamoDB and SQS mocked via `moto`

To run a specific test file:

```bash
poetry run pytest tests/unit/test_time_filtering.py -v
```

## Deployment

**Deploy to the default `dev` stage:**

```bash
npx serverless deploy
```

**Deploy to a specific stage:**

```bash
npx serverless deploy --stage prod
```

**Remove the stack:**

```bash
npx serverless remove --stage dev
```

### Environment Variables

| Variable           | Description                                                    |
|--------------------|----------------------------------------------------------------|
| `TABLE_NAME`       | DynamoDB table name (set automatically by Serverless)          |
| `QUEUE_URL`        | SQS queue URL (set automatically by Serverless)                |
| `PROVISIONING_URL` | HTTP endpoint called by the worker Lambda for each permission  |

Override `PROVISIONING_URL` per stage in `serverless.yml` under `provider.environment`.

## Utility Scripts

### Generate mock data

```bash
cd script
python generate_data.py
```

Generates ~500k permission records (20 tenants × 100 users × 5–500 permissions) to `script/permissions.data` in JSON Lines format.

### Load data into DynamoDB

```bash
cd script
python load_data.py --table permissions-dev --region us-east-1
```

Reads `permissions.data` and writes it to DynamoDB using concurrent `batch_write_item` calls.

Options:

| Flag        | Default           | Description                      |
|-------------|-------------------|----------------------------------|
| `--table`   | `permissions-dev` | DynamoDB table name              |
| `--region`  | `us-east-1`       | AWS region                       |
| `--workers` | `10`              | Number of concurrent threads     |
| `--file`    | `permissions.data`| Path to the JSON Lines data file |

## JWT Token Requirements

All endpoints require an `Authorization: Bearer <token>` header. The token must contain:

| Claim       | Required by                                       |
|-------------|---------------------------------------------------|
| `tenant_id` | All endpoints                                     |
| `sub`       | `GET /permissions/me` only                        |

> **Note:** In this exercise implementation, JWT signatures are **not validated**. In a production system, use a proper authorizer (e.g., AWS Cognito, a custom Lambda authorizer with signature verification).

## Schedule Time Window Behavior

- All times are in **UTC**.
- Weekday `0` = Monday, `6` = Sunday.
- Overnight windows are supported: a `start_time` of `"22:00"` with `end_time` of `"06:00"` is active from 22:00 until 06:00 the next day.
- A permission with `schedule: null` is always active regardless of the current time.
- For `GET /permissions/me`, only `Active` permissions whose schedule window matches the current time are considered. The response contains the deduplicated, sorted list of their `permission` action strings.
