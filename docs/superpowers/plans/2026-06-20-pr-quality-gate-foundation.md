# PR Quality Gate Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI, React, PostgreSQL, Alembic, Docker Compose foundation for PR Quality Gate Dashboard through Fase 2 plus GitHub read-only Fase 2.5.

**Architecture:** Backend uses synchronous FastAPI, SQLAlchemy, PostgreSQL UUID/enums/JSONB, Alembic, and service modules. Frontend uses Vite React TypeScript with a typed `fetch` client and CSS-only dashboard views.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL, pytest, React, TypeScript, Vite, Docker Compose.

---

### Task 1: Backend Test Harness

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/tests/test_repositories.py`
- Create: `backend/tests/test_quality_gate_config.py`
- Create: `backend/tests/test_analysis_runs.py`
- Create: `backend/tests/test_github_errors.py`

- [ ] Write pytest fixtures that reset PostgreSQL tables before each test and expose a FastAPI `TestClient`.
- [ ] Write failing tests for health, repository CRUD/default config, config update, mock analysis scenarios, and missing GitHub token errors.
- [ ] Run pytest and verify tests fail because backend modules are missing.

### Task 2: Backend Foundation

**Files:**
- Create backend package, app factory, config, DB session, models, schemas, services, routes, requirements, Dockerfile, Alembic config, migration.

- [ ] Implement settings, database base/session, FastAPI app, CORS, and `/health`.
- [ ] Implement SQLAlchemy models with UUID primary keys, native enums, JSONB fields, relationships, and timestamps.
- [ ] Implement Alembic initial migration matching models.
- [ ] Implement repository, quality gate, analysis, and GitHub read-only services/routes.
- [ ] Run pytest until backend tests pass.

### Task 3: Frontend Foundation

**Files:**
- Create Vite React TypeScript app under `frontend/`.

- [ ] Implement typed API client with snake_case DTOs.
- [ ] Implement dashboard, repository list/create, repository detail, config form, analysis history, mock scenario creation, PR listing, and analysis detail.
- [ ] Add CSS-only application styling.
- [ ] Run TypeScript build.

### Task 4: Local Environment and Docs

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `README.md`

- [ ] Wire backend, frontend, and postgres in Docker Compose.
- [ ] Make backend run `alembic upgrade head` before `uvicorn` in local Compose.
- [ ] Document module responsibilities, setup, endpoints, scenarios, and validation checklist.
- [ ] Run final available verification commands and report any environment limitations.
