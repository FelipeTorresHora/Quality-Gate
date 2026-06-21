# GitHub PR Context Trigger Design

## Scope

Build Fase 3 as GitHub PR Context plus Pull Request Trigger. The phase expands the current GitHub read-only integration from repository validation and open Pull Request listing into Pull Request context capture and automatic Analysis Run creation.

Fase 3 does not implement real quality gates. It prepares the input evidence and trigger path that later Coverage Gate, Security Gate, Technical Debt Gate, and LangChain phases will consume.

## Goals

The dashboard can fetch Pull Request context on demand, receive signed GitHub Pull Request webhooks, capture stable snapshots for a known repository, and create or reuse a pending Analysis Run for each Pull Request head SHA.

The dashboard should be able to show that an automatic run was created because of a GitHub Pull Request event, even before the real analyzers exist.

## Non-Goals

Fase 3 does not publish GitHub comments or commit statuses. GitHub write-back remains a later publication phase.

Fase 3 does not add OAuth, GitHub App installation, per-user GitHub tokens, organization tenancy, background workers, Redis, scheduler polling, Coverage Gate, Security Gate, Technical Debt Gate, LangChain execution, or real gate decisions.

## Architecture

The backend remains a synchronous FastAPI service. GitHub calls stay inside `GitHubClient` and continue to use one global `GITHUB_TOKEN` from `.env`.

The phase adds two GitHub-facing paths:

- manual PR context read: `GET /api/repositories/{repository_id}/pull-requests/{pr_number}/context`;
- signed webhook ingest: `POST /api/github/webhooks`.

The manual endpoint is read-only and does not create an Analysis Run. The webhook endpoint validates the raw GitHub signature, filters events and actions, enriches Pull Request data through the GitHub API, then creates or reuses an Analysis Run.

Webhook processing stays synchronous and short. Fase 3 does not introduce queues or workers. If enrichment fails after the event is accepted as valid and relevant, the backend records an error Analysis Run instead of returning an error that encourages GitHub retries.

## Domain Model

`AnalysisRun` remains the dashboard-owned record for one attempt to evaluate a Pull Request. Fase 3 extends it with trigger and context evidence:

- `trigger_source`: persisted enum with `mock`, `manual`, and `github_webhook`;
- `pull_request_snapshot_json`: JSONB metadata for the Pull Request state captured for this run;
- `changed_files_snapshot_json`: JSONB list of changed files and per-file patch metadata;
- `diff_snapshot`: text diff captured for the run;
- `diff_truncated`: boolean flag showing whether `diff_snapshot` was truncated.

The persisted invariant is one Analysis Run per `repository_id`, `pr_number`, and `head_sha`. Replayed webhooks and repeated events for the same commit return the existing run. New commits on the same Pull Request create new pending runs.

## Pull Request Context

The Pull Request Snapshot includes stable metadata needed by later gates and UI:

- PR number, title, body, state, draft flag, author login, HTML URL;
- base branch, head branch, head SHA, base SHA if available;
- created and updated timestamps.

The Changed File Snapshot includes the GitHub changed-file fields needed by later gates:

- `filename`;
- `status`;
- `additions`;
- `deletions`;
- `changes`;
- `patch` when GitHub returns it.

The raw diff is captured as text up to 5 MB. If the diff exceeds 5 MB, the service stores the first 5 MB, sets `diff_truncated = true`, and still creates the run. Large diffs are not a trigger failure.

## Webhook Behavior

The webhook endpoint always requires a configured `GITHUB_WEBHOOK_SECRET` and a valid `X-Hub-Signature-256` HMAC signature over the raw request body.

Only GitHub `pull_request` events are in scope. The following actions can trigger an Analysis Run:

- `opened`;
- `reopened`;
- `synchronize`;
- `ready_for_review`.

All other Pull Request actions are ignored. Closed and merged Pull Requests are ignored in Fase 3.

Draft Pull Requests are ignored until `ready_for_review`. `synchronize` events for draft Pull Requests are ignored. After a Pull Request is ready for review, `synchronize` creates or reuses a run by head SHA.

Webhooks for repositories not already registered in the dashboard are ignored. The backend responds with an accepted ignored result rather than creating repositories automatically.

## Error Handling

Invalid signatures return a stable error and do not create an Analysis Run.

Missing webhook secret is a configuration error and the endpoint must not accept unsigned payloads.

Unsupported events, unsupported actions, draft PRs, and unknown repositories return accepted ignored responses with stable reasons.

If a relevant event is valid but GitHub enrichment fails because of rate limit, permissions, missing PR data, or GitHub service failure, the backend creates or reuses an Analysis Run with:

- `status = error`;
- `decision = null`;
- `trigger_source = github_webhook`;
- `error_message` containing a stable user-facing explanation.

The webhook response remains `202 accepted` for these processing failures because the event was received and recorded.

## Frontend

The current repository detail page remains the main surface. It lists webhook-created runs alongside mock and future manual runs.

The analysis history shows enough trigger context to distinguish runs:

- PR number;
- run status;
- gate decision when present;
- score when present;
- trigger source;
- head SHA;
- created time.

The analysis detail page shows a Pull Request Context section when snapshots exist:

- PR title, author, branches, head SHA, and GitHub URL;
- changed file count;
- changed file list with status, additions, deletions, and patch availability.

The frontend does not render the full raw diff in Fase 3. Large diff display is deferred to avoid loading up to 5 MB of text into the initial UI.

## Configuration and Documentation

`.env.example` includes:

- `GITHUB_TOKEN`;
- `GITHUB_WEBHOOK_SECRET`;
- `GITHUB_DEFAULT_BASE_BRANCH`;
- `GITHUB_STATUS_CONTEXT`;
- future OpenAI and LangSmith variables.

The README explains how to obtain the GitHub token, webhook secret, OpenAI API key, and LangSmith API key. The detailed local webhook tunnel test instructions are added when `/api/github/webhooks` is implemented.

## Testing

Backend tests cover:

- manual PR context endpoint with mocked GitHub responses;
- changed-file and diff mapping;
- 5 MB diff truncation behavior;
- missing token errors;
- missing webhook secret errors;
- invalid webhook signature errors;
- unsupported events and actions returning ignored responses;
- draft Pull Request ignoring rules;
- unknown repository ignoring rules;
- `opened`, `reopened`, `synchronize`, and `ready_for_review` creating or reusing pending runs;
- idempotency for `repository_id + pr_number + head_sha`;
- enrichment failures creating `status = error` runs.

Frontend verification covers TypeScript build and rendering of trigger source plus Pull Request context from Analysis Run detail payloads.

## Success Criteria

Fase 3 is complete when:

1. a registered repository can expose Pull Request context through the manual endpoint;
2. a signed GitHub Pull Request webhook can create a pending Analysis Run;
3. repeated delivery for the same Pull Request head SHA does not duplicate runs;
4. new commits create a new pending run;
5. relevant context snapshots are persisted on Analysis Run;
6. oversized diffs are truncated at 5 MB without failing the trigger;
7. the dashboard shows webhook-created runs and Pull Request context;
8. README and `.env.example` describe the required credentials clearly.
