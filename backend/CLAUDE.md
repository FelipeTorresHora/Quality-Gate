# CLAUDE.md (backend)

Scope: `backend/`. Read root `CLAUDE.md` first for cross-cutting architecture.

## Commands

```bash
pytest                                          # full suite, needs Postgres at DATABASE_URL
pytest tests/test_repositories.py               # one file
pytest tests/test_repositories.py::test_name    # one test
alembic upgrade head
alembic revision --autogenerate -m "message"
```

No lint/format config in repo (no ruff/black/mypy config files) — match existing style by hand, don't introduce a new tool without asking.

## Tests (`tests/`)

- `conftest.py` sets the test `DATABASE_URL` before importing `app`, so environment setup must happen before app imports.
- `reset_database` fixture drops+recreates all tables per test (full isolation, no transactions/rollback tricks) and `pytest.skip`s the test if Postgres is unreachable rather than failing — don't "fix" that skip, it's intentional for environments without Postgres.
- `client` fixture is a plain `TestClient(app)`.
- `repository` fixture creates a GitHub App installation, synchronized repository, admin access, and authenticated session directly through the installation/session services.
- Test files are flat functions, no classes, one file per resource (`test_repositories.py`, `test_quality_gate_config.py`, `test_analysis_runs.py`, `test_github_errors.py`, `test_health.py`).

## Adding a new resource

1. Model in `app/models/`, import it at the bottom of `app/db/base.py`.
2. `alembic revision --autogenerate -m "..."`, check the generated migration before applying — autogenerate misses some constraint/enum diffs.
3. Pydantic schemas in `app/schemas/`.
4. Service function(s) in `app/services/`: raise `AppError` for all expected failures, call `repository_service.get_repository()` (or equivalent) first when scoped to a repository so 404s stay consistent.
5. Thin route in `app/api/routes_*.py`, no logic beyond calling the service and setting `response_model`/`status_code`.
6. Register the router in `app/main.py` if it's a new module.

## Gotchas

- Repositories and their default configs are created by GitHub installation synchronization; there are no public repository creation routes.
- `AnalysisRunStatus` (pending/running/completed/error) and `GateDecision` (pass/fail) are separate columns on `AnalysisRun`. Manual live PR analysis and webhook runs use the real execution pipeline.
- `GitHubClient` (`app/services/github_service.py`) has no retry/backoff and is synchronous (`httpx.get`, not async) — keep it that way unless adding a real async analyzer that needs it.
- GitHub operations use short-lived installation tokens. Do not add `GITHUB_TOKEN` back as a product integration path.
