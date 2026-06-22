# Dashboard Phase 4 Design

## Scope

Build Fase 4 as the operational dashboard maturity phase. The phase improves the current React dashboard into a cohesive workflow for repositories, Pull Requests, Quality Gate Config, mock Analysis Runs, analysis history, and analysis detail.

Fase 4 does not implement real Coverage Gate, Security Gate, Technical Debt Gate, LangChain analysis, GitHub comments, GitHub commit statuses, authentication, GitHub App installation, queues, workers, or persisted analytics snapshots.

## Product Direction

The dashboard should feel like a working Pull Request review console, not a marketing page. It uses `design.md` as the visual baseline, adapted for dense operational screens.

The phase keeps the existing foundation and GitHub read-only behavior. It does not replace mock analysis with real analysis. Any action that creates an Analysis Run during this phase must remain explicit that it is a mock workflow.

## Visual System

The UI uses the `design.md` language as an operational system:

- near-black canvas for the application shell;
- charcoal lifted surfaces for cards, tables, forms, and panels;
- white pill primary buttons;
- charcoal pill secondary buttons;
- accent blue reserved for links, focus rings, and selected states;
- gradients used sparingly as highlight cards, not section backgrounds;
- semantic status badges for Run Status, Gate Decision, severity, and blocking state;
- `letter-spacing: 0` for dashboard legibility.

The dashboard must not use a marketing hero as the first screen. Large display typography is acceptable only where it does not reduce scanability of tables, forms, or status panels.

## Navigation

The main application navigation keeps two primary destinations:

- `Dashboard`;
- `Repositories`.

Repository detail becomes a workspace with route-backed tabs:

- `/repositories/:repository_id/pull-requests`;
- `/repositories/:repository_id/quality-gate-config`;
- `/repositories/:repository_id/analysis-runs`.

`/repositories/:repository_id` redirects to `/repositories/:repository_id/pull-requests`.

Each repository workspace page shows a shared context header with repository `full_name`, default branch, GitHub/manual source, and relevant actions.

## Dashboard Summary

The dashboard initial page becomes a real global metrics panel backed by a new aggregate backend endpoint. The backend calculates the summary in real time from existing tables and does not persist metrics in a new table.

The Dashboard Summary includes:

- total Repositories;
- total Analysis Runs;
- counts by Run Status;
- counts by Gate Decision;
- approval rate for completed runs with a Gate Decision;
- recent Analysis Runs;
- Analysis Finding counts by category and severity;
- top blocking categories when findings exist.

The Dashboard Summary is global in Fase 4. It does not include repository filters, team filters, or date range filters.

## Pull Request Workspace

The Pull Requests tab acts as a review queue. Each row shows:

- Pull Request number;
- title;
- author;
- draft/state;
- head branch and base branch;
- current `head_sha`;
- Pull Request Review State;
- action to create a mock Analysis Run.

Pull Request Review State is derived from the latest relevant Analysis Run for that Pull Request. The backend should return the review state with the Pull Request list so the frontend does not need to reconstruct domain rules from separate calls.

If the latest Analysis Run for a PR has the same `head_sha` as the live Pull Request, the row can show that run's Run Status, Gate Decision, score, trigger source, and link to detail.

If the latest Analysis Run has a different `head_sha`, the row must mark the state as outdated, using language such as `Outdated` or `New commits`. A stale passing run must not appear to approve the current Pull Request state.

The phase 4 action label must remain explicit, such as `Run Mock Analysis` or `Create Mock Analysis`. It should not say `Analyze PR` until real gates exist.

## Quality Gate Config Workspace

The Quality Gate Config tab keeps the existing fields but groups them by domain pillar:

- Coverage: minimum total coverage, maximum coverage drop, minimum changed-files coverage;
- Security: blocking severities;
- Technical Debt: max function lines, max complexity, fail on new TODO;
- GitHub Publishing: comment on GitHub and publish GitHub status toggles.

The UI should save through the existing Quality Gate Config update endpoint unless backend validation changes are required. Field names remain aligned with existing API payloads.

## Analysis History Workspace

The Analysis History tab lists Analysis Runs for the current Repository. The table includes:

- Pull Request number;
- Run Status;
- Gate Decision;
- score;
- trigger source;
- head SHA;
- created time;
- link to Analysis Run detail.

The history view remains repository-scoped. Global recent runs appear only in the Dashboard Summary.

## Analysis Run Detail

The Analysis Run detail page prioritizes interpreted information over raw JSON.

The top summary shows:

- Run Status;
- Gate Decision;
- score;
- trigger source;
- Pull Request number;
- head SHA;
- timestamps;
- operational error message when present.

When Pull Request Snapshot and Changed File Snapshot data exist, the page shows PR title, author, branches, GitHub link, changed file count, and changed file list.

The main body shows pillar summaries for Coverage, Security, and Technical Debt using the existing JSON snapshots. These summaries should extract statuses, counts, blocking reasons, warnings, and suggestions when present.

Analysis Findings are a primary section, with category, severity, blocking state, title, description, file path, and line number.

The final report markdown remains visible as the generated report. Raw JSON remains available as a secondary diagnostic section and must not dominate the page.

## Empty, Loading, and Error States

Fase 4 treats empty states and errors as required UI paths. The frontend must handle:

- no Repository records;
- missing or invalid GitHub token;
- manual repository without GitHub Pull Requests;
- no open Pull Requests;
- no Analysis Runs;
- no Analysis Findings;
- Analysis Run with `status = error`;
- API request failure;
- initial loading states.

Messages should be short and actionable. They should show the state and the next available action without long in-app explanations.

## Backend API Changes

Fase 4 adds a dashboard summary endpoint, for example:

`GET /api/dashboard/summary`

The response should be typed in backend Pydantic schemas and frontend TypeScript DTOs.

Fase 4 should also expose Pull Requests with their Pull Request Review State. This can be implemented either by extending the current repository Pull Request endpoint or by adding a dashboard-specific endpoint. The chosen endpoint must keep the latest-run matching logic in backend service code.

No new persistence table is required for Dashboard Summary or Pull Request Review State.

## Testing

Backend tests cover:

- Dashboard Summary with no data;
- Dashboard Summary with pass, fail, pending/running/error runs;
- approval rate calculation;
- finding aggregation by category and severity;
- Pull Request Review State with no run;
- Pull Request Review State matching current `head_sha`;
- Pull Request Review State marked outdated when `head_sha` differs.

Frontend verification covers:

- TypeScript build;
- dashboard metrics rendering;
- repository workspace route navigation;
- Quality Gate Config grouped form rendering;
- Pull Request row review states;
- Analysis Run detail interpreted pillar summaries;
- empty and error states.

## Success Criteria

Fase 4 is complete when:

1. the dashboard initial page shows global aggregate metrics from the backend;
2. repository detail uses route-backed tabs for Pull Requests, Quality Gate Config, and Analysis History;
3. Pull Request rows show their current Pull Request Review State;
4. stale Analysis Runs are visibly marked outdated when PR head SHA changes;
5. mock analysis actions are labeled as mock;
6. Quality Gate Config is grouped by pillar;
7. Analysis Run detail prioritizes interpreted summaries over raw JSON;
8. required empty, loading, and error states are implemented;
9. the UI applies `design.md` as an operational dark dashboard system;
10. backend and frontend verification pass for the new phase 4 behavior.
