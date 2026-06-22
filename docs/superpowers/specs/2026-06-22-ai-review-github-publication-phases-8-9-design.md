# AI Review And GitHub Publication Phases 8-9 Design

## Scope

Build Fases 8 and 9 as the smallest useful layer on top of the existing real Gate Execution path.

Fase 8 adds a LangChain-backed AI Review Snapshot, an AI score, and a final Markdown report after Coverage Gate, Security Gate, and Technical Debt Gate have completed. The AI review explains the evidence; it does not own the final Gate Decision.

Fase 9 adds manual GitHub Publication for completed or errored Analysis Runs. Publication can create or update a Pull Request comment and publish a commit status using the existing repository Quality Gate Config flags.

## Non-Goals

These phases do not add background workers, queues, automatic publish-on-execute, GitHub App installation, OAuth, per-user GitHub credentials, retry tables, LangGraph, LangSmith evaluation datasets, automatic code patches, Slack/Discord notifications, or persistent publication history.

AI review does not run when required gates fail operationally. In that case, the dashboard can still show partial Gate Result Snapshots and a deterministic final report, but no AI score is required.

GitHub Publication does not mutate Run Status, Gate Decision, Gate Result Snapshots, Analysis Findings, or AI Review Snapshot. Publication failure is an operational failure of the publish endpoint, not a quality result.

## Product Direction

After Fases 5-7, the dashboard can answer whether a captured Pull Request passed the configured policies. Fase 8 makes that result easier to understand. Fase 9 lets the user intentionally send that result back to GitHub.

The intended MVP flow is:

```text
Pending Analysis Run
-> user executes analysis
-> gates produce snapshots and findings
-> backend applies objective Gate Decision
-> LangChain produces AI Review Snapshot when configured and possible
-> backend saves final Markdown report
-> dashboard shows result
-> user publishes result to GitHub when desired
```

The minimal complexity rule is that each phase is synchronous and explicit. Analysis remains one API call. GitHub Publication is a separate API call.

## Domain Model

`AI Review Snapshot` is the structured interpretation produced by the LangChain review step for a completed Gate Execution. It is stored as historical evidence for the Analysis Run and is used for summary, score, risks, and suggestions.

`Gate Decision` remains objective. If any completed gate fails, the Analysis Run decision is `fail`; if all completed gates pass, the decision is `pass`; if any required gate errors, there is no decision. The AI review cannot override this.

`GitHub Publication` is the dashboard action of publishing an Analysis Run result to GitHub as a Pull Request comment, commit status, or both.

## Persistence Changes

Add one JSONB column to `analysis_runs`:

```text
ai_review_json JSONB NOT NULL DEFAULT '{}'
```

No new publication table is added in the MVP.

Existing fields keep their roles:

- `score`: nullable display score, copied from the AI Review Snapshot when generated;
- `final_report_markdown`: final human-readable report for dashboard rendering and GitHub comments;
- `coverage_result_json`, `security_result_json`, `technical_debt_result_json`: objective per-pillar Gate Result Snapshots;
- `decision`: objective Gate Decision.

## AI Review Snapshot Shape

The initial stored shape is:

```json
{
  "status": "generated",
  "model": "gpt-4.1-mini",
  "generated_at": "2026-06-22T12:00:00Z",
  "score": 72,
  "summary": "The PR is useful but blocked by coverage and technical debt.",
  "risk_level": "medium",
  "blocking_reasons": [
    "Coverage for changed files is below the configured threshold."
  ],
  "suggestions": [
    "Add tests for the changed service path."
  ],
  "coverage_assessment": "Coverage failed because changed-file coverage is low.",
  "security_assessment": "No blocking security findings were detected.",
  "technical_debt_assessment": "The PR adds a function above the configured size limit."
}
```

Allowed `status` values:

```text
generated
skipped
error
```

If `OPENAI_API_KEY` is missing, store:

```json
{
  "status": "skipped",
  "reason": "openai_api_key_missing"
}
```

If the model call fails or returns invalid structured output, store:

```json
{
  "status": "error",
  "reason": "ai_review_failed",
  "message": "AI review could not be generated."
}
```

AI review errors do not change `Run Status` or `Gate Decision`. When AI review is skipped or errors, `score` remains null and the backend still writes a deterministic `final_report_markdown`.

## AI Review Inputs

The agent input should be assembled by backend code from persisted Analysis Run evidence:

- Pull Request Snapshot;
- Changed File Snapshot;
- diff snapshot, capped to the first 60000 characters for the MVP;
- `diff_truncated`;
- Gate Result Snapshots;
- Analysis Findings;
- Quality Gate Config;
- Coverage Execution Config language and report format.

The prompt must state that Gate Decision is objective and already determined by the backend. The agent may explain blockers and suggest fixes, but it must not invent a different final decision.

The AI input builder should not include application secrets, GitHub tokens, OpenAI keys, LangSmith keys, or full command environment values.

## Backend Architecture

Add a focused agent package:

```text
app/services/agent/
  quality_agent.py
  prompts.py
  schemas.py
```

Responsibilities:

- `schemas.py`: Pydantic models for structured AI Review Snapshot output;
- `prompts.py`: prompt text and formatting helpers;
- `quality_agent.py`: LangChain call, structured output validation, and fallback snapshot creation.

Add a final report service:

```text
app/services/report_service.py
```

Responsibilities:

- build Markdown from Gate Decision, gate snapshots, findings, and AI Review Snapshot;
- produce a deterministic report when AI review is skipped or fails;
- produce an operational-error report when Gate Execution errors before AI review can run.

Update `analysis_execution_service.execute_analysis_run`:

```text
run coverage gate
run security gate
run technical debt gate
if any gate errors:
    save deterministic operational-error report
    finish Run Status = error
else:
    apply objective Gate Decision
    generate AI Review Snapshot
    copy generated score to analysis_runs.score
    generate final_report_markdown
    finish Run Status = completed
```

The service remains synchronous for the MVP.

## Final Report Markdown

The final report must be generated for completed runs even when AI review is unavailable.

The report should include:

- title with PASS, FAIL, or operational error;
- Gate Decision when present;
- score when present;
- short summary;
- Coverage section;
- Security section;
- Technical Debt section;
- blocking reasons;
- suggestions;
- footer identifying the dashboard context.

For GitHub comments, the report body should include a stable hidden marker:

```markdown
<!-- ai-quality-gate:analysis-run:{analysis_run_id} -->
```

This lets GitHub Publication update an existing dashboard comment for the same Analysis Run instead of creating duplicates.

## GitHub Publication Behavior

Add an endpoint:

```http
POST /api/analysis-runs/{analysis_run_id}/publish-github
```

The endpoint publishes only channels enabled by the repository Quality Gate Config:

- `comment_on_github = true`: create or update a Pull Request comment;
- `publish_github_status = true`: create a commit status on `analysis_run.head_sha`.

If both flags are false, the endpoint returns a successful response with both channels skipped. The frontend should hide or disable the publish action when both channels are disabled.

Publication is allowed only for:

```text
Run Status = completed
Run Status = error
```

Publication is rejected for:

```text
pending
running
```

## GitHub Client Changes

Extend `GitHubClient` with:

```text
list_issue_comments(owner, name, pr_number)
create_issue_comment(owner, name, pr_number, body)
update_issue_comment(owner, name, comment_id, body)
create_commit_status(owner, name, sha, state, context, description)
```

The comment APIs use GitHub issue comments because Pull Request comments live on the issue comments endpoint.

Commit status mapping:

```text
Gate Decision pass -> success
Gate Decision fail -> failure
Run Status error -> error
```

The status context uses `GITHUB_STATUS_CONTEXT`, defaulting to `ai-quality-gate`.

The status description should be short:

```text
Quality gate passed.
Quality gate failed.
Quality gate could not complete.
```

No `target_url` is required for the local MVP.

## Publication Response

Use a small response shape:

```json
{
  "analysis_run_id": "uuid",
  "comment": {
    "enabled": true,
    "published": true,
    "html_url": "https://github.com/org/repo/pull/42#issuecomment-1",
    "skipped_reason": null
  },
  "commit_status": {
    "enabled": true,
    "published": true,
    "target_sha": "abc123",
    "state": "failure",
    "skipped_reason": null
  }
}
```

When a channel is disabled, return `published = false` and a stable skipped reason such as `comment_disabled` or `status_disabled`.

GitHub API failures should return stable Operational Errors using the existing error response style. If a retry is needed, updating comments by marker keeps retries from creating duplicate comments for the same Analysis Run.

## API Changes

Extend `AnalysisRunDetail` with:

```text
ai_review_json
```

Add:

```http
POST /api/analysis-runs/{analysis_run_id}/publish-github
```

Response model:

```text
GitHubPublicationResult
```

No standalone "run AI review" endpoint is added. AI review is part of successful Gate Execution.

## Frontend Changes

The Analysis Run detail page should show:

- AI summary when `ai_review_json.status = generated`;
- score when present;
- risk level when present;
- suggestions from `ai_review_json`;
- fallback report content when AI review is skipped or errored;
- final Markdown report;
- Publish to GitHub action when the run is completed or errored.

The publish action should show which channels were published or skipped. It should not imply that GitHub Publication changes the Analysis Run result.

## Configuration

Existing settings remain:

```text
OPENAI_API_KEY
OPENAI_MODEL
LANGSMITH_TRACING
LANGSMITH_API_KEY
LANGSMITH_PROJECT
GITHUB_TOKEN
GITHUB_STATUS_CONTEXT
```

No new environment variable is required for Fases 8 and 9.

When `OPENAI_API_KEY` is missing, AI review is skipped and the deterministic report still renders. When `GITHUB_TOKEN` is missing, GitHub Publication returns the existing stable GitHub token error.

## Error Handling

AI review failure:

- does not make the Analysis Run `error`;
- stores `ai_review_json.status = error`;
- leaves `score = null`;
- produces deterministic `final_report_markdown`.

Gate execution failure:

- keeps existing semantics: `Run Status = error`, `Gate Decision = null`;
- does not invoke AI review;
- stores a deterministic operational-error report.

GitHub Publication failure:

- does not mutate Analysis Run result fields;
- returns an Operational Error from the publish endpoint;
- may be retried by the user.

## Testing

Backend tests should cover:

- Alembic migration adds `ai_review_json` with default `{}`;
- `AnalysisRunDetail` includes `ai_review_json`;
- completed passing run stores generated AI Review Snapshot and score when the agent succeeds;
- completed failing run stores generated AI Review Snapshot and preserves objective `decision = fail`;
- AI review skipped when `OPENAI_API_KEY` is missing;
- AI review error does not change completed run decision;
- operational gate error does not invoke AI review and writes deterministic report;
- final report contains PASS, FAIL, and operational-error variants;
- publish endpoint rejects pending and running runs;
- publish endpoint skips both channels when both config flags are false;
- publish endpoint creates or updates the marked Pull Request comment when comments are enabled;
- publish endpoint creates commit status with `success`, `failure`, and `error` mappings;
- GitHub token missing returns the stable token error.

Frontend verification should cover:

- TypeScript build;
- Analysis detail rendering for generated, skipped, and errored AI review snapshots;
- publish action display for published and skipped channels.

## Success Criteria

Fases 8 and 9 are complete when:

1. `analysis_runs` stores `ai_review_json`;
2. successful Gate Execution produces an AI Review Snapshot when OpenAI is configured;
3. AI Review Snapshot never overrides objective Gate Decision;
4. completed runs receive a final Markdown report;
5. AI review failures still produce deterministic reports;
6. errored gate executions produce deterministic operational-error reports;
7. the dashboard renders AI summary, score, suggestions, and final report;
8. `POST /api/analysis-runs/{analysis_run_id}/publish-github` exists;
9. enabled GitHub comment publication creates or updates one marked PR comment per Analysis Run;
10. enabled GitHub status publication posts the expected commit status state;
11. disabled publication channels are skipped clearly;
12. backend tests and frontend TypeScript build pass.

## Related Decisions

- `docs/adr/0003-separate-run-status-from-gate-decision.md`
- `docs/adr/0026-save-partial-gate-results-on-execution-error.md`
- `docs/adr/0027-require-all-gates-for-final-decision.md`
- `docs/adr/0028-execute-existing-analysis-runs.md`
- `docs/adr/0029-execute-only-pending-analysis-runs.md`
- `docs/adr/0032-keep-langchain-out-of-final-gate-decision.md`
- `docs/adr/0033-store-ai-review-snapshot-on-analysis-run.md`
- `docs/adr/0034-use-manual-github-publication-for-mvp.md`
