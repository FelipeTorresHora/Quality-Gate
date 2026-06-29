# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PR Quality Gate Dashboard — evaluates whether a GitHub Pull Request passes a quality gate across coverage, security, technical debt, and optional AI review. The product path is now GitHub App/OAuth only: users sign in with GitHub, synchronize repositories from GitHub App installations, analyze live Pull Requests manually or from Pull Request Triggers, and may publish GitHub comments/statuses.

Mock Analysis Runs and manual repository creation are not supported. Analysis Runs are created only from GitHub App Pull Request events or from Manual Pull Request Analysis on a selected live Pull Request. See `CONTEXT.md` for exact glossary/terminology used across code, commits, and PRs.

## Commands

Run everything via Docker Compose (backend runs `alembic upgrade head` before `uvicorn` on every start):

```bash
cp .env.example .env      # optional
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (health: `/health`)

Backend (from `backend/`, venv already at `backend/.venv`):

```bash
pytest                              # full suite
pytest tests/test_repositories.py   # single file
pytest tests/test_repositories.py::test_create_repository  # single test
alembic upgrade head                # apply migrations
alembic revision --autogenerate -m "message"  # new migration
```

Tests require a real Postgres reachable at `TEST_DATABASE_URL` or the default `postgresql+psycopg://pr_quality:pr_quality@localhost:55432/pr_quality_test`; `reset_database` fixture in `tests/conftest.py` drops/creates all tables per test and `pytest.skip`s if Postgres is unreachable. `docker-compose.yml` publishes Postgres on host port `55432` by default and seeds a test DB via `docker/postgres/init-test-db.sql`.

Frontend (from `frontend/`):

```bash
npm run dev       # vite dev server
npm run build     # tsc -b && vite build
npm run preview
```

## Architecture

**Backend** (`backend/app`, FastAPI + SQLAlchemy 2.0 + Alembic + Postgres):

- `main.py` wires routers and registers a single exception handler for `AppError`.
- `core/errors.py` — `AppError(status_code, code, message)` is the only error type services raise; the global handler turns it into `{"detail": {"code", "message"}}`. Don't raise bare `HTTPException` in services — raise `AppError` and let the handler format it.
- `core/config.py` — `Settings` (pydantic-settings) loaded once via `get_settings()` (`lru_cache`). By default it reads `.env`; tests set `PR_QUALITY_ENV_FILE=` to avoid developer env leakage.
- `db/base.py` — `Base` (DeclarativeBase); imports every model module at the bottom so Alembic's autogenerate sees all tables. Add new models here.
- `db/session.py` — engine/`SessionLocal`; `get_db()` is the FastAPI dependency.
- `models/` — one file per table, using `UUIDPrimaryKeyMixin` (UUID PK, `mixins.py`) and `TimestampMixin` (`created_at`/`updated_at`) almost everywhere. Enums (`models/enums.py`) are persisted as native Postgres enums via a shared `enum_values()` helper — keep that pattern when adding new enum columns. JSONB columns (`quality_gate_config.security_fail_on`, `analysis_run.*_result_json`) hold flexible/snapshot data by design (see `docs/adr/0001`, `0002`).
- `services/` — all business logic and the only layer allowed to raise `AppError` or touch the DB session directly; routes are thin pass-throughs. `repository_service` is the dependency other services call into (e.g. `quality_gate_service`/`analysis_service`/`github_service` all call `get_repository()` first to 404 consistently).
- `api/routes_*.py` — one router per resource, included in `main.py`. No business logic here.
- `schemas/` — Pydantic request/response models, decoupled from ORM models.
- `services/analysis_service.py` — creates/reuses Analysis Runs from captured live Pull Request context. Keep one run per repository, PR number, and head SHA.
- `services/analysis_execution_service.py` — executes Coverage, Security, and Technical Debt gates sequentially, records partial snapshots/findings on failure, generates optional AI review, and builds the final report.
- `services/github_service.py` — `GitHubClient` wraps GitHub REST using GitHub App installation tokens for repository access, Pull Request context, comments, and commit statuses. Maps GitHub API failures into stable `AppError` codes.

Domain model relationships: `Repository` 1:1 `QualityGateConfig` and 1:1 `CoverageExecutionConfig`, `Repository` 1:N `AnalysisRun`, `AnalysisRun` 1:N `AnalysisFinding`. `User`, `GitHubConnection`, `GitHubAppInstallation`, `InstallationRepository`, and `UserRepositoryAccess` model GitHub OAuth login and installation-derived authorization.

Architectural decisions are recorded in `docs/adr/` — check there before changing JSONB usage, UUID PKs, enum representation, or the run-status/gate-decision split (`AnalysisRunStatus` is operational state; `GateDecision` is the pass/fail outcome — never conflate them).

**Frontend** (`frontend/src`, React 19 + TypeScript + Vite + react-router v7):

- `api/client.ts` — single typed fetch wrapper (`request<T>`); throws `ApiError` (status + `{code, message}`) on non-2xx. Add new endpoints here, not ad-hoc fetches in components.
- `types/api.ts` — DTOs shared across pages/components; keep in sync with backend Pydantic schemas.
- `pages/` — one page per route: `DashboardPage`, `RepositoriesPage`, `RepositoryDetailPage` (config + PRs + history), `AnalysisDetailPage`. Routes are declared in `App.tsx`.
- `components/` — small reusable display components (`StatusBadge`, `ErrorMessage`).
- No state library/query cache — pages fetch directly via `api/client.ts`.

## Conventions

- Repository identity is `owner/name` (`full_name`), unique; `github_repo_id` is nullable (manual repos have none).
- New tables/columns: add the SQLAlchemy model under `models/`, import it in `db/base.py`, then generate an Alembic migration — don't hand-write migrations from scratch when autogenerate can do it.
- Keep PT-BR domain terms out of code/identifiers but match `CONTEXT.md` glossary in comments, commit messages, and docs.
