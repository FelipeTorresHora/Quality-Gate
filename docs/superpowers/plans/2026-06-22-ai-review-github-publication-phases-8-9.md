# Fases 8-9 AI Review E Publicacao GitHub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add synchronous AI review snapshots and manual GitHub publication on top of completed or errored Analysis Runs.

**Architecture:** Gate Execution remains the objective source of the final decision. A focused AI agent module explains completed gate evidence, a report module renders deterministic Markdown, and a separate publication module writes comments/statuses to GitHub only when explicitly requested.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL JSONB, LangChain, OpenAI, pytest, React, TypeScript, Vite.

---

## Implementation Tasks

- [ ] Add `analysis_runs.ai_review_json` persistence and API/frontend contracts.
- [ ] Add LangChain-backed AI review snapshot generation with stable skipped/error fallbacks.
- [ ] Add deterministic final report generation for pass, fail, and operational error runs.
- [ ] Wire AI review and final report into `execute_analysis_run` without allowing AI to change objective decisions.
- [ ] Add manual GitHub publication endpoint, service, schemas, and client methods for issue comments and commit statuses.
- [ ] Render AI review and GitHub publication UI on the Analysis Run detail page.
- [ ] Verify with backend pytest and frontend TypeScript build.

## Assumptions

- Publication uses global `GITHUB_TOKEN`; no per-user credentials are added.
- Publication is manual only and never runs inside Gate Execution.
- No publication history table is added for this MVP.
- Frontend verification remains `npm run build` plus manual browser checks.
