# Auto-Publish Webhook-Triggered Runs

Accepted on 2026-07-26. Supersedes ADR-0034's manual-only scope. The worker now calls the existing `github_publication_service` right after a `GITHUB_WEBHOOK`-triggered Analysis Run finishes execution (`completed` or `error`), publishing the Pull Request comment and/or commit status automatically. Manual Pull Request Analysis runs are unaffected — they still require the explicit dashboard publish action.

**Decision**

The publish call lives in `worker.process_next_job()`, wrapped in its own try/except, after `analysis_queue.complete()`. A publish failure is logged but never re-queues or fails the analysis job — Gate Execution already succeeded, and publication is a best-effort side effect of it, not part of the Analysis Run decision model. This keeps `analysis_execution_service` and `github_publication_service` decoupled, exactly as ADR-0034 anticipated ("automatic publication can be added later around the same publication service without changing the Analysis Run decision model").

**Consequences**

Repositories with `comment_on_github`/`publish_github_status` disabled behave exactly as before (`github_publication_service` already no-ops per flag). Manual Pull Request Analysis keeps requiring an explicit publish action, so a user re-running analysis on demand does not spam the Pull Request. `AnalysisTriggerSource.GITHUB_WEBHOOK` is the sole switch; no new config flag was introduced to gate the automation itself.
