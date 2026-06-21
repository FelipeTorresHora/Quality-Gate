# PR Quality Gate Foundation Design

## Scope

Build the PR Quality Gate Dashboard foundation through Fase 2, with Fase 2.5 as the first GitHub read-only extension. The foundation answers whether the dashboard can persist repositories, edit quality gate policy, create scenario-based mock analysis runs, and display results end to end.

Fase 2.5 validates that the app can read real GitHub Pull Requests with a configured token. It does not perform real analysis, store Pull Requests, comment on GitHub, publish commit statuses, implement OAuth, or install a GitHub App.

## Architecture

The app is a local Docker Compose stack with `backend`, `frontend`, and `postgres`. The backend is a synchronous FastAPI service using SQLAlchemy sessions, Alembic migrations, PostgreSQL UUID primary keys, PostgreSQL enums for domain states, and JSONB for flexible policy/result snapshots. The frontend is a Vite React TypeScript dashboard with a small typed `fetch` API client and CSS-only styling.

## Domain Model

`Repository` represents a global GitHub repository identity, unique by `full_name`. It is not owned by `User` during the foundation build. `User` and `GitHubConnection` exist as future identity scaffolding but are not wired into repository ownership or UI flows.

Every `Repository` has exactly one `QualityGateConfig`, created with defaults. `AnalysisRun` stores one dashboard-owned evaluation attempt for a Pull Request number and head SHA. `AnalysisFinding` stores queryable issues for a run. Gate result snapshots remain on `AnalysisRun` as JSONB.

`AnalysisRun.status` is operational: `pending`, `running`, `completed`, or `error`. `AnalysisRun.decision` is the quality outcome: `pass`, `fail`, or null. Technical failures use `status = error`, `decision = null`, and `error_message`.

## API

`GET /health` returns `{ "status": "ok" }`. All application endpoints live under `/api` with snake_case payloads.

Repositories support list/create/detail. Creating a repository manually creates its default quality gate config. Quality gate config can be read and updated. Analysis runs can be listed, created from controlled mock scenarios, and fetched by ID. Fase 2.5 adds repository validation and open PR listing through GitHub read-only endpoints backed by `GITHUB_TOKEN`.

## Mock Analysis

Mock analysis is scenario-controlled, not random. Initial scenarios are `passing`, `coverage_fail`, `security_fail`, `technical_debt_fail`, and `mixed_fail`. Each creates a completed run with decision, score, JSONB result snapshots, markdown report, and findings.

## GitHub Read-only

The first GitHub integration uses one global `GITHUB_TOKEN` from `.env`. Users register repositories by `owner/name`; the backend validates access with GitHub and stores the repository identity. PRs are listed live from GitHub and are not stored. Public and private repositories are supported when the token has permission. GitHub errors return stable structured codes and clear messages.

## Frontend

The UI has dashboard, repository list, repository detail, quality gate editing, analysis history, PR listing when GitHub read-only is configured, and analysis detail. The repository detail page keeps config, PRs, and history in one context to avoid premature navigation complexity.

## Testing

Backend tests cover health, repository creation with default config, quality gate updates, mock analysis scenarios, and structured GitHub configuration errors. Tests run against PostgreSQL because the model depends on JSONB and native enums.
