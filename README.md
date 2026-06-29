# PR Quality Gate Dashboard

GitHub App dashboard for evaluating Pull Requests across coverage, security,
technical debt, and an optional AI review.

## Scope

- GitHub OAuth login with server-side sessions.
- Per-user repository access synchronized from GitHub App installations.
- Installation tokens for API calls, clone, Pull Request comments, and commit
  statuses.
- Live Pull Request queue with manual Analyze actions.
- Signed Pull Request webhooks with automatic background execution.
- Configurable coverage, security, technical debt, and GitHub publication
  policies, including per-repository gate enablement.
- PostgreSQL persistence managed by SQLAlchemy and Alembic.
- React dashboard and Docker Compose development environment.

Mock Analysis Runs are no longer supported. Analysis Runs are created only from
GitHub App Pull Request events or from the Analyze action on a live GitHub Pull
Request.

## Run Locally

Create the local environment file:

```bash
cp .env.example .env
```

Configure the GitHub App values described below, then run:

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/health

The backend runs `alembic upgrade head` before FastAPI starts.

Docker Compose publishes PostgreSQL on host port `55432` by default to avoid
colliding with a local PostgreSQL on `5432`. Override it with
`POSTGRES_HOST_PORT` if needed. The backend container receives
`BACKEND_DATABASE_URL` as its internal `DATABASE_URL`, so host-side
`DATABASE_URL` values do not accidentally point the container at `localhost`.

## GitHub App Setup

The product uses one GitHub App for user login, installation access, webhooks,
Pull Request context, Git clone, comments, and commit statuses.

Configure the GitHub App with:

- Homepage URL: `http://localhost:5173`
- Callback URL: `http://localhost:8000/api/auth/github/callback`
- Webhook URL: `{public-backend-url}/api/github/webhooks`
- Webhook secret: the same value as `GITHUB_WEBHOOK_SECRET`
- Repository permissions:
  - Metadata: read
  - Contents: read
  - Pull requests: write
  - Commit statuses: write
- Events:
  - Pull request
  - Installation
  - Installation repositories
  - GitHub App authorization

Set the App ID, OAuth client credentials, slug, webhook secret, and either the
private key value or a private key path in `.env`:

```env
GITHUB_APP_ID=
GITHUB_APP_CLIENT_ID=
GITHUB_APP_CLIENT_SECRET=
GITHUB_APP_PRIVATE_KEY=
GITHUB_APP_PRIVATE_KEY_PATH=
GITHUB_APP_SLUG=
GITHUB_WEBHOOK_SECRET=
```

Do not commit real values copied into `.env`. If a client secret, webhook
secret, private key, token, or OpenAI key is copied into a tracked file, issue,
log, or Pull Request, rotate it in the provider dashboard before continuing.

For local webhook delivery, expose port `8000` with a tunnel:

```bash
ngrok http 8000
```

Then use the resulting HTTPS URL plus `/api/github/webhooks` as the GitHub App
webhook URL.

Official references:

- [Creating a GitHub App](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app)
- [GitHub App permissions](https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps)
- [Validating webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)

## Session And Token Secrets

Use random values outside local throwaway environments:

```powershell
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

Set that result as `SESSION_SECRET`. Generate the Fernet encryption key used for
stored GitHub OAuth tokens with:

```powershell
.\backend\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set the result as `TOKEN_ENCRYPTION_KEY`. Enable `SESSION_COOKIE_SECURE=true`
when the frontend and backend are served over HTTPS.

## Analysis Flow

1. Sign in with GitHub.
2. Install or manage the GitHub App from the Repositories page.
3. Open a synchronized repository and select a live Pull Request.
4. Select Analyze, or let a supported Pull Request webhook trigger the run.
5. Review deterministic gate evidence, findings, AI review, and the final report.
6. Optionally publish the report as a Pull Request comment or commit status.

Pull Request webhook actions `opened`, `reopened`, `synchronize`, and
`ready_for_review` create or reuse one run per repository, PR number, and head
SHA. Draft and closed Pull Requests are ignored.

The Analyze action executes synchronously. Webhook runs are scheduled with
FastAPI background tasks in the backend process.

## Gate Execution

The runner creates a temporary workspace, clones with a short-lived GitHub App
installation token, checks out the captured base and head SHAs, runs the
configured coverage command, and executes security and technical debt gates.

Coverage execution is configured per repository. Defaults include:

- Python: `pytest --cov=. --cov-report=xml:coverage.xml`
- TypeScript/JavaScript: `npm test -- --coverage`
- Go: `go test ./... -coverprofile=coverage.out`

Security tooling may include Bandit, Semgrep, detect-secrets, and dependency
audit tools. Repository commands run in the backend service environment, not in
a dedicated per-run container. Only analyze repositories you trust.

The provided backend Docker image installs `git`, Python security scanners,
Node/npm, and Go so the default Python, JavaScript/TypeScript, and Go coverage
commands have a usable local runner. Repositories with extra native packages,
alternate package managers, or custom language runtimes should extend the
backend image or adjust the per-repository Coverage Execution Config.

## AI Review

Set `OPENAI_API_KEY` to enable the optional structured AI review:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

Without a key, deterministic gates still run and the AI review is recorded as
skipped. LangSmith tracing is optional.

## Main API

- `GET /health`
- `GET /api/auth/me`
- `GET /api/auth/github/login`
- `GET /api/auth/github/callback`
- `POST /api/auth/logout`
- `GET /api/github/installations`
- `GET /api/github/installations/install-url`
- `POST /api/github/webhooks`
- `GET /api/repositories`
- `GET /api/repositories/{repository_id}`
- `GET /api/repositories/{repository_id}/pull-requests`
- `GET /api/repositories/{repository_id}/pull-requests/{pr_number}/context`
- `POST /api/repositories/{repository_id}/pull-requests/{pr_number}/analyze`
- `GET /api/repositories/{repository_id}/quality-gate-config`
- `PUT /api/repositories/{repository_id}/quality-gate-config`
- `GET /api/repositories/{repository_id}/coverage-execution-config`
- `PUT /api/repositories/{repository_id}/coverage-execution-config`
- `GET /api/repositories/{repository_id}/analysis-runs`
- `GET /api/analysis-runs/{analysis_run_id}`
- `POST /api/analysis-runs/{analysis_run_id}/execute`
- `POST /api/analysis-runs/{analysis_run_id}/publish-github`

## Verification

Backend:

```powershell
docker compose up -d postgres
cd backend
.\.venv\Scripts\python.exe -m pytest tests
```

The test suite defaults to
`postgresql+psycopg://pr_quality:pr_quality@localhost:55432/pr_quality_test`.
Set `TEST_DATABASE_URL` explicitly only when you want to use a different test
database.

Frontend:

```powershell
cd frontend
npm run build
```
