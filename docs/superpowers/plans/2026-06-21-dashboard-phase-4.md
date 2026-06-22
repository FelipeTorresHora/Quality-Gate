# Dashboard Phase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Implement Fase 4 as a dark operational dashboard for repositories, Pull Requests, Quality Gate Config, mock Analysis Runs, analysis history, and analysis detail.

**Architecture:** Add backend read-only aggregate/query services without new persistence tables. Extend the existing Pull Request endpoint with backend-derived review state. Split the current repository detail frontend into route-backed workspace tabs and apply `design.md` as a dense dark dashboard system.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, PostgreSQL, pytest, React, TypeScript, Vite, CSS.

---

## Public API And Type Changes

- Add `GET /api/dashboard/summary`.
  - Response DTO: `DashboardSummaryRead`.
  - Fields: `total_repositories`, `total_analysis_runs`, `run_status_counts`, `gate_decision_counts`, `approval_rate`, `recent_analysis_runs`, `finding_counts`, `top_blocking_categories`.
  - Counts include zero values for all run statuses and gate decisions.
  - `approval_rate` is `null` when there are no completed runs with a Gate Decision; otherwise percentage rounded to 1 decimal.

- Extend `GET /api/repositories/{repository_id}/pull-requests`.
  - Keep current Pull Request fields.
  - Add `review_state`.
  - `review_state.state` values: `not_run`, `current`, `outdated`.
  - `review_state.analysis_run` includes latest run metadata when one exists: `id`, `status`, `decision`, `score`, `trigger_source`, `head_sha`, `created_at`.
  - Rule: if latest run SHA differs from live PR `head_sha`, return `outdated`; frontend must not show that decision as current approval.

- Add matching frontend DTOs in `frontend/src/types/api.ts`.
  - `DashboardSummary`, `DashboardRecentAnalysisRun`, `DashboardFindingCount`, `DashboardBlockingCategory`.
  - `PullRequestReviewState`, `PullRequestReviewRun`.
  - Update `GitHubPullRequest` to include `review_state`.

---

## Implementation Tasks

### Task 1: Backend Dashboard Summary

**Files:**
- Create `backend/app/schemas/dashboard.py`
- Create `backend/app/services/dashboard_service.py`
- Create `backend/app/api/routes_dashboard.py`
- Modify `backend/app/main.py`
- Create `backend/tests/test_dashboard_summary.py`

- [ ] Write failing pytest coverage for empty summary.
- [ ] Write failing pytest coverage for pass/fail/pending/running/error run status counts.
- [ ] Write failing pytest coverage for approval rate using only completed runs with non-null decision.
- [ ] Write failing pytest coverage for finding counts by category and severity.
- [ ] Write failing pytest coverage for top blocking categories.
- [ ] Implement `DashboardSummaryRead` and nested DTOs in `schemas/dashboard.py`.
- [ ] Implement real-time SQLAlchemy aggregate queries in `dashboard_service.py`; do not create a metrics table or migration.
- [ ] Implement `GET /api/dashboard/summary` in `routes_dashboard.py`.
- [ ] Register the router in `main.py`.
- [ ] Run `cd backend; pytest tests/test_dashboard_summary.py -q`.

### Task 2: Pull Request Review State

**Files:**
- Modify `backend/app/schemas/github.py`
- Create `backend/app/services/pull_request_review_service.py`
- Modify `backend/app/services/github_service.py`
- Modify `backend/app/api/routes_repositories.py`
- Modify or add tests in `backend/tests/test_github_errors.py` and `backend/tests/test_repositories.py`

- [ ] Write failing tests for PR list with no run returning `review_state.state = "not_run"`.
- [ ] Write failing tests for latest run matching current `head_sha` returning `current` plus run metadata.
- [ ] Write failing tests for latest run with different `head_sha` returning `outdated`.
- [ ] Write failing test that manual repositories return an empty PR list without requiring `GITHUB_TOKEN`.
- [ ] Update missing-token test to use a GitHub-source repository (`github_repo_id` present).
- [ ] Add review-state DTOs to `schemas/github.py`.
- [ ] Implement latest-run lookup by repository and PR number, ordered by `created_at desc`.
- [ ] Extend `github_service.list_repository_pull_requests` to return PRs with review state.
- [ ] Keep all SHA comparison logic in backend service code, not frontend.
- [ ] Run `cd backend; pytest tests/test_repositories.py tests/test_github_errors.py -q`.

### Task 3: Frontend API Client And Routing

**Files:**
- Modify `frontend/src/types/api.ts`
- Modify `frontend/src/api/client.ts`
- Modify `frontend/src/App.tsx`
- Modify `frontend/src/pages/RepositoryDetailPage.tsx`
- Create `frontend/src/pages/RepositoryPullRequestsPage.tsx`
- Create `frontend/src/pages/RepositoryQualityGateConfigPage.tsx`
- Create `frontend/src/pages/RepositoryAnalysisRunsPage.tsx`
- Create `frontend/src/components/EmptyState.tsx`
- Create `frontend/src/components/LoadingBlock.tsx`

- [ ] Add dashboard and PR review DTOs.
- [ ] Add `getDashboardSummary()` to the API client.
- [ ] Keep all API calls through `request<T>()`.
- [ ] Convert `RepositoryDetailPage` into a repository workspace layout with shared header, source badge, default branch, actions, and `<Outlet />`.
- [ ] Add route-backed tabs:
  - `/repositories/:repositoryId/pull-requests`
  - `/repositories/:repositoryId/quality-gate-config`
  - `/repositories/:repositoryId/analysis-runs`
- [ ] Redirect `/repositories/:repositoryId` to `/repositories/:repositoryId/pull-requests`.
- [ ] Update existing repository links to point at the workspace root or PR tab.
- [ ] Add loading and empty-state components with short actionable copy.

### Task 4: Dashboard Summary Page

**Files:**
- Modify `frontend/src/pages/DashboardPage.tsx`

- [ ] Replace health/repository-count placeholder metrics with `getDashboardSummary()`.
- [ ] Render total repositories, total analysis runs, status counts, decision counts, approval rate, recent runs, finding matrix, and top blocking categories.
- [ ] Link recent runs to `/analysis-runs/:analysisRunId`.
- [ ] Show empty state when no repositories or no runs exist.
- [ ] Keep the page operational and dense; no marketing hero.

### Task 5: Repository Workspace Tabs

**Files:**
- Implement tab pages created in Task 3.
- Modify `frontend/src/components/StatusBadge.tsx`

- [ ] Pull Requests tab: render PR number, title, author, draft/state, branches, current head SHA, review state, latest run metadata, detail link, and `Run Mock Analysis`.
- [ ] Pull Requests tab: show `Outdated` or `New commits` when review state is stale; do not display stale `pass` as current approval.
- [ ] Pull Requests tab: keep mock scenario selector and manual mock run form for manual repositories or non-GitHub flows.
- [ ] Quality Gate Config tab: group existing fields under Coverage, Security, Technical Debt, and GitHub Publishing.
- [ ] Quality Gate Config tab: save through existing `PUT /api/repositories/{id}/quality-gate-config`.
- [ ] Analysis History tab: render repository-scoped runs with PR number, status, decision, score, trigger source, head SHA, created time, and detail link.
- [ ] Update status badge classes for `not_run`, `current`, `outdated`, `blocking`, severities, statuses, decisions, and trigger sources.

### Task 6: Analysis Run Detail

**Files:**
- Modify `frontend/src/pages/AnalysisDetailPage.tsx`

- [ ] Keep top summary focused on status, decision, score, trigger source, PR number, head SHA, timestamps, and error message.
- [ ] Render PR snapshot when present: title, author, branches, GitHub link, changed file count, and changed file list.
- [ ] Add interpreted pillar summaries before raw JSON:
  - Coverage: status, total/base/PR coverage, changed-files coverage, coverage drop, blocking reasons.
  - Security: status, critical/high/medium/low counts, blocking reasons.
  - Technical Debt: status, score, blocking reasons, suggestions.
- [ ] Make Analysis Findings a primary section before final report.
- [ ] Keep final report markdown visible.
- [ ] Move raw JSON snapshots into a secondary diagnostic section.

### Task 7: Visual System And Required States

**Files:**
- Modify `frontend/src/styles/app.css`
- Reuse existing components where possible.

- [ ] Apply near-black app canvas, charcoal surfaces, white primary pill buttons, charcoal secondary pill buttons, accent blue for links/focus/selected tabs only.
- [ ] Keep dashboard typography legible with `letter-spacing: 0`.
- [ ] Use 8px panel/card radius; use pill radius only for buttons and badges.
- [ ] Avoid full-section gradients; if used, keep gradients to one small highlight card.
- [ ] Implement states for: no repositories, missing/invalid GitHub token, manual repository without GitHub PRs, no open PRs, no analysis runs, no findings, `status = error`, API request failure, and initial loading.

### Task 8: Verification And Commit Checkpoints

- [ ] Backend targeted tests:
  - `cd backend; pytest tests/test_dashboard_summary.py -q`
  - `cd backend; pytest tests/test_repositories.py tests/test_github_errors.py -q`
  - `cd backend; pytest tests/test_analysis_runs.py tests/test_github_webhooks.py -q`
- [ ] Backend full suite:
  - `cd backend; pytest -q`
- [ ] Frontend build:
  - `cd frontend; npm run build`
- [ ] Local workflow check:
  - `docker compose up --build`
  - Open `http://localhost:5173`.
  - Verify Dashboard, Repositories, PR tab, Config tab, History tab, and Analysis Run detail.

---

## Assumptions And Defaults

- No database migration is needed because Fase 4 derives metrics from existing tables.
- The existing Pull Request endpoint is extended instead of adding a dashboard-specific PR endpoint.
- Manual repositories return no GitHub Pull Requests and still allow explicit mock Analysis Run creation.
- Missing or invalid GitHub token remains an API error for GitHub-source repositories.
- No frontend test runner is introduced; verification is TypeScript build plus manual browser checks.
- No real Coverage Gate, Security Gate, Technical Debt Gate, LangChain analysis, GitHub comments/statuses, auth, queues, workers, or persisted analytics snapshots are added in this phase.
