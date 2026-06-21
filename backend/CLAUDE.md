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

- `conftest.py` sets `DATABASE_URL`/`GITHUB_TOKEN` env defaults before importing `app`, so it must stay the first import in any test file that needs the app.
- `reset_database` fixture drops+recreates all tables per test (full isolation, no transactions/rollback tricks) and `pytest.skip`s the test if Postgres is unreachable rather than failing — don't "fix" that skip, it's intentional for environments without Postgres.
- `client` fixture is a plain `TestClient(app)`.
- `repository` fixture creates one repo via the real `POST /api/repositories` endpoint (not a DB insert) — tests build state through the API, not by reaching into the ORM. Follow that pattern for new fixtures.
- Test files are flat functions, no classes, one file per resource (`test_repositories.py`, `test_quality_gate_config.py`, `test_analysis_runs.py`, `test_github_errors.py`, `test_health.py`).

## Adding a new resource

1. Model in `app/models/`, import it at the bottom of `app/db/base.py`.
2. `alembic revision --autogenerate -m "..."`, check the generated migration before applying — autogenerate misses some constraint/enum diffs.
3. Pydantic schemas in `app/schemas/`.
4. Service function(s) in `app/services/`: raise `AppError` for all expected failures, call `repository_service.get_repository()` (or equivalent) first when scoped to a repository so 404s stay consistent.
5. Thin route in `app/api/routes_*.py`, no logic beyond calling the service and setting `response_model`/`status_code`.
6. Register the router in `app/main.py` if it's a new module.

## Gotchas

- `QualityGateConfig` is created automatically inside `repository_service.create_repository` — never create one manually elsewhere.
- `AnalysisRunStatus` (pending/running/completed/error) and `GateDecision` (pass/fail) are separate columns on `AnalysisRun` — mock runs currently jump straight to `COMPLETED` with a decision already set; don't assume `RUNNING`/`PENDING` ever transition anywhere yet (no real runner exists).
- `GitHubClient` (`app/services/github_service.py`) has no retry/backoff and is synchronous (`httpx.get`, not async) — keep it that way unless adding a real async analyzer that needs it.
- Settings in `.env.example` reference future scanner/runner config (`DEFAULT_TEST_COMMAND`, `RUN_BANDIT`, etc.) that `app/core/config.py` does **not** read yet — don't assume those env vars are wired up.
