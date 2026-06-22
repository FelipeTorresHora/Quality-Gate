# PR Quality Gate Dashboard

Foundation for a dashboard that evaluates whether a Pull Request passes a quality gate across coverage, security, and technical debt.

## Scope

This repo currently implements the MVP tecnico de fundacao plus GitHub Read-only Basico plus the first synchronous real Gate Execution path:

- FastAPI backend with health check, repositories, quality gate config, coverage execution config, analysis history, mock scenarios, GitHub read-only PR listing/context, signed Pull Request webhook triggers, and explicit pending-run execution.
- React dashboard with repository creation, config editing, PR listing, mock analysis creation, real pending-run execution, trigger-aware history, and analysis detail with captured Pull Request context.
- PostgreSQL models managed by SQLAlchemy and Alembic.
- Docker Compose for backend, frontend, and Postgres.

Not included yet: LangChain execution, AI scoring, GitHub comments/statuses, Redis, workers, GitHub App, billing, per-run containers, or production deploy.

## Run Locally

Optionally create a local env file:

```bash
cp .env.example .env
```

Then run:

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/health

The backend runs `alembic upgrade head` before starting FastAPI in the local Compose environment.

## Environment Variables

Create `.env` from `.env.example` and fill only the keys needed for the phase you are running.

```bash
cp .env.example .env
```

### GitHub token

`GITHUB_TOKEN` is currently used to validate repositories and list open Pull Requests. For Fase 3, the same token will also read Pull Request details, changed files, and diff context.

Recommended setup:

1. Open the GitHub personal access token page: https://github.com/settings/personal-access-tokens.
2. Create a fine-grained token.
3. Limit repository access to the repositories you will connect to the dashboard.
4. Grant read access for repository metadata, Pull Requests, and contents.
5. Copy the token into `.env`:

```env
GITHUB_TOKEN=github_pat_xxxxxxxxxxxxxxxxxxxx
```

Official references:

- GitHub personal access tokens: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- GitHub fine-grained token permissions: https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens

### GitHub webhook secret

`GITHUB_WEBHOOK_SECRET` is required by the Pull Request webhook endpoint. The backend rejects unsigned payloads and validates GitHub's `X-Hub-Signature-256` HMAC signature against the raw request body.

Generate a random secret locally:

```powershell
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

Put the generated value in `.env`:

```env
GITHUB_WEBHOOK_SECRET=your-random-secret
```

Configure a repository webhook in GitHub:

- Payload URL: your public backend URL plus `/api/github/webhooks`
- Content type: `application/json`
- Secret: the same value as `GITHUB_WEBHOOK_SECRET`
- Events: Pull requests

For local development, expose `http://localhost:8000` with a tunnel such as ngrok or cloudflared, then use the public tunnel URL as the webhook base URL.

Example local flow:

```bash
docker compose up --build
ngrok http 8000
```

If ngrok prints `https://example.ngrok-free.app`, configure the GitHub webhook Payload URL as:

```text
https://example.ngrok-free.app/api/github/webhooks
```

Open, reopen, synchronize, or mark a Pull Request as ready for review. The dashboard creates or reuses one pending Analysis Run for the registered repository, PR number, and head SHA. Draft Pull Requests, unknown repositories, unsupported events, and unsupported actions are accepted but ignored.

### Real Gate Execution

Webhook-created Analysis Runs start as `pending`. Execute them explicitly through the dashboard or:

```bash
curl -X POST http://localhost:8000/api/analysis-runs/{analysis_run_id}/execute
```

Execution is synchronous in the backend process. The backend creates a temporary workspace, clones the repository, checks out the captured base and head SHAs, runs configured coverage commands, runs deterministic security and technical debt gates, then stores normalized snapshots and findings.

Runner environment variables:

```env
WORKDIR=/tmp/pr-quality-dashboard
COMMAND_TIMEOUT_SECONDS=600
KEEP_WORKDIR=false
```

Important MVP risk: repository commands run in the backend/local service environment, not in a dedicated per-run container. Only execute code from repositories you trust in this phase. The runner strips app secrets such as GitHub, OpenAI, LangSmith, and `DATABASE_URL` from child process environment variables, but this is not a complete sandbox.

Coverage execution is configured per repository through:

- `GET /api/repositories/{repository_id}/coverage-execution-config`
- `PUT /api/repositories/{repository_id}/coverage-execution-config`

Initial defaults:

- Python: `pip install -r requirements.txt`, `pytest --cov=. --cov-report=xml:coverage.xml`, `coverage.xml`, `cobertura_xml`
- TypeScript: `npm ci`, `npm test -- --coverage`, `coverage/lcov.info`, `lcov`
- JavaScript: `npm ci`, `npm test -- --coverage`, `coverage/lcov.info`, `lcov`
- Go: `go mod download`, `go test ./... -coverprofile=coverage.out`, `coverage.out`, `go_coverprofile`

Required local tooling depends on the repository language and configured gates:

- Coverage: pytest/coverage.py for Python, npm test coverage with LCOV for JavaScript/TypeScript, Go toolchain for Go.
- Generic security scanners: Semgrep and detect-secrets.
- Python security scanners: Bandit and pip-audit.

Official references:

- GitHub webhook signature validation: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
- GitHub webhook events and headers: https://docs.github.com/en/webhooks/webhook-events-and-payloads

### OpenAI API key

`OPENAI_API_KEY` is reserved for the future LangChain agent phase. It is not required for the current foundation build or Fase 3 GitHub PR context work.

Create an API key in the OpenAI dashboard, then add it to `.env`:

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4.1-mini
```

Official reference: https://developers.openai.com/api/docs/quickstart

### LangSmith API key

LangSmith is optional tracing/observability for future LangChain work. Leave it disabled unless you are actively tracing agent runs.

```env
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=pr-quality-dashboard
```

To enable it later, create a LangSmith API key and set:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_xxxxxxxxxxxxxxxxxxxx
```

Official reference: https://docs.langchain.com/langsmith/create-account-api-key

## Backend Modules

- `backend/app/main.py`: FastAPI app, CORS, routes, error handler.
- `backend/app/core`: settings and structured application errors.
- `backend/app/db`: SQLAlchemy engine/session and model metadata.
- `backend/app/models`: SQLAlchemy models for users, GitHub connections, repositories, quality gate configs, analysis runs, and findings.
- `backend/app/schemas`: Pydantic request/response schemas.
- `backend/app/services`: repository, quality gate, analysis, and GitHub read-only application logic.
- `backend/app/api`: route modules.
- `backend/alembic`: migration environment and initial schema migration.

## Frontend Modules

- `frontend/src/api/client.ts`: typed fetch client for the FastAPI API.
- `frontend/src/types/api.ts`: shared API DTO types.
- `frontend/src/pages`: dashboard, repository list, repository detail, and analysis detail views.
- `frontend/src/components`: reusable status and error display components.
- `frontend/src/styles/app.css`: lightweight dashboard styling.

## API

- `GET /health`
- `GET /api/repositories`
- `POST /api/repositories`
- `POST /api/repositories/github`
- `GET /api/repositories/{repository_id}`
- `GET /api/repositories/{repository_id}/pull-requests`
- `GET /api/repositories/{repository_id}/pull-requests/{pr_number}/context`
- `GET /api/repositories/{repository_id}/quality-gate-config`
- `PUT /api/repositories/{repository_id}/quality-gate-config`
- `GET /api/repositories/{repository_id}/coverage-execution-config`
- `PUT /api/repositories/{repository_id}/coverage-execution-config`
- `GET /api/repositories/{repository_id}/analysis-runs`
- `POST /api/repositories/{repository_id}/analysis-runs/mock`
- `GET /api/analysis-runs/{analysis_run_id}`
- `POST /api/analysis-runs/{analysis_run_id}/execute`
- `POST /api/github/webhooks`

## Mock Scenarios

`POST /api/repositories/{repository_id}/analysis-runs/mock` accepts:

```json
{
  "scenario": "mixed_fail",
  "pr_number": 42,
  "head_sha": "abc123"
}
```

Supported scenarios:

- `passing`
- `coverage_fail`
- `security_fail`
- `technical_debt_fail`
- `mixed_fail`

## Validation Checklist

- `docker compose up --build` starts Postgres, backend, and frontend.
- `GET /health` returns `{ "status": "ok" }`.
- A repository can be created manually.
- Each repository gets a default quality gate config.
- Quality gate config can be edited.
- Mock analysis runs can be created by scenario.
- Analysis history and details can be viewed.
- With `GITHUB_TOKEN` configured, a repository can be validated through GitHub and open PRs can be listed.
- With `GITHUB_TOKEN` configured, a registered repository can expose Pull Request context.
- With `GITHUB_WEBHOOK_SECRET` configured, signed Pull Request webhooks create or reuse pending runs by PR head SHA.
