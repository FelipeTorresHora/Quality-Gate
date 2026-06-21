# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PR Quality Gate Dashboard — evaluates whether a Pull Request passes a quality gate across coverage, security, and technical debt. Currently at the "MVP tecnico de fundacao" + "GitHub Read-only Basico" stage (see `CONTEXT.md` for exact glossary/terminology used across code, commits, and PRs — use these terms, not synonyms like "execution", "check", or "scanner config").

Not implemented yet: real PR analysis, LangChain execution, coverage/security scanners, webhooks, GitHub comments/status checks, Redis, workers, GitHub App, billing, auth. Analysis runs today are only created via mock scenarios.

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

Tests require a real Postgres reachable at `DATABASE_URL` (default `postgresql+psycopg://pr_quality:pr_quality@localhost:5432/pr_quality_test`); `reset_database` fixture in `tests/conftest.py` drops/creates all tables per test and `pytest.skip`s if Postgres is unreachable. `docker-compose.yml` seeds a test DB via `docker/postgres/init-test-db.sql`.

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
- `core/config.py` — `Settings` (pydantic-settings) loaded once via `get_settings()` (`lru_cache`). All env vars (DB, GitHub token, OpenAI/LangSmith placeholders for future analyzers) live here.
- `db/base.py` — `Base` (DeclarativeBase); imports every model module at the bottom so Alembic's autogenerate sees all tables. Add new models here.
- `db/session.py` — engine/`SessionLocal`; `get_db()` is the FastAPI dependency.
- `models/` — one file per table, using `UUIDPrimaryKeyMixin` (UUID PK, `mixins.py`) and `TimestampMixin` (`created_at`/`updated_at`) almost everywhere. Enums (`models/enums.py`) are persisted as native Postgres enums via a shared `enum_values()` helper — keep that pattern when adding new enum columns. JSONB columns (`quality_gate_config.security_fail_on`, `analysis_run.*_result_json`) hold flexible/snapshot data by design (see `docs/adr/0001`, `0002`).
- `services/` — all business logic and the only layer allowed to raise `AppError` or touch the DB session directly; routes are thin pass-throughs. `repository_service` is the dependency other services call into (e.g. `quality_gate_service`/`analysis_service`/`github_service` all call `get_repository()` first to 404 consistently).
- `api/routes_*.py` — one router per resource, included in `main.py`. No business logic here.
- `schemas/` — Pydantic request/response models, decoupled from ORM models.
- `services/analysis_service.py` — `SCENARIOS` dict holds the fixed mock analysis fixtures (`passing`, `coverage_fail`, `security_fail`, `technical_debt_fail`, `mixed_fail`). This is the only way analysis runs are created today; there is no real analyzer.
- `services/github_service.py` — `GitHubClient` wraps GitHub REST with a Bearer token from settings; read-only (repo lookup, list open PRs). Maps 401/403+ratelimit→429, 403→`github_token_forbidden`, 404→`github_repository_not_found`. No OAuth, no GitHub App, no writes back to GitHub yet.

Domain model relationships: `Repository` 1:1 `QualityGateConfig` (auto-created on repo creation, cascade delete), `Repository` 1:N `AnalysisRun`, `AnalysisRun` 1:N `AnalysisFinding`. `User`/`GitHubConnection` exist as scaffolding for future auth, intentionally uncoupled from `Repository` ownership (`docs/adr/0005`, `0006`).

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
