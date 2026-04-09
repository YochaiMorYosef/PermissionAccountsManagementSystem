# Permissions Service — Candidate Exercise

Welcome! This exercise is based on a real-world serverless permissions service. Read through the `README.md` to understand the system before you start.

---

## Prerequisites

Make sure the following are installed before you begin:

- [Node.js](https://nodejs.org/) 18+
- [Python](https://www.python.org/) 3.13
- [Poetry](https://python-poetry.org/) 1.8

---

## Guidance

- **Use an LLM.** You are encouraged (and expected) to use an AI assistant to help you solve this exercise. How you use it is part of what we observe.
- **This is a git repository.** Commit your changes as you go, as you normally would in a real project.
- **Submitting:** When you are done, zip the entire repository — including the `.git` folder — and send us the zip file.
- **Task 5** should be answered in a file named `future-enhancements.md` at the root of the `exercise` folder.

---

## Tasks

### 1. Deploy and verify

Deploy the project and confirm that all endpoints are working correctly. You can use your AWS account or LocalStack (in both cases it should remain in the free tier)

Install dependencies first:

```bash
npm install
poetry install
```

Then deploy:

```bash
npx serverless deploy
```

Once deployed, populate the database with the prepared test data:

```bash
python script/load_data.py --table permissions-dev
```

> **Note:** The system integrates with an external provisioning service that is already deployed for you. Its URL is pre-configured in `serverless.yml` under `PROVISIONING_URL` — you do not need to deploy or modify it.

### 2. Build a UI

Create a web UI for the service. It should include:

- A management screen where a user can **create, view, update, and delete** permissions.
- A separate screen where the authenticated user can look up their **currently active permissions** for a specific account.

### 3. Add role-based access control

Restrict API access based on a `role` claim in the JWT token:

- Users with the `admin` role can call all endpoints (create, update, delete, view).
- Regular users (no `admin` role) can only call `GET /permissions/me` to view their own active permissions.

Requests that violate this rule should be rejected with an appropriate HTTP error.

### 4. Find and fix a bug

Something is wrong in the system. Some of those users clearly _do_ have permissions in the database, yet the API returns an empty list for them.

Investigate the root cause and fix it.

### 5. Suggest improvements

Review the system as a whole and write down what you would do to make it better — more robust, scalable, maintainable, or anything else. There are no wrong answers — we're interested in how you think about production systems.
