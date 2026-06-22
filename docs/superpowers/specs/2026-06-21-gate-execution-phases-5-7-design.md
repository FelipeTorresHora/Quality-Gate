# Gate Execution Phases 5-7 Design

## Scope

Build Fases 5-7 as the first real Gate Execution path for pending Analysis Runs. The phase replaces mock-only analysis with deterministic Coverage Gate, Security Gate, and Technical Debt Gate execution while keeping the current synchronous FastAPI architecture.

This phase covers:

- Coverage Gate for Python, TypeScript, JavaScript, and Go;
- Security Gate with generic scanners and Python-specific checks;
- Technical Debt Gate with deterministic rules;
- execution against existing Analysis Runs;
- repository-owned Coverage Execution Config;
- normalized Gate Result Snapshots and Analysis Findings.

## Non-Goals

Fases 5-7 do not implement LangChain, AI architecture review, AI scoring, final report generation, GitHub comments, GitHub commit statuses, background workers, Redis, per-run containers, GitHub App installation, OAuth, multi-user auth, or automatic webhook-triggered execution.

Webhook-created Analysis Runs remain pending until a user explicitly executes them. The Pull Request Trigger prepares evidence; it does not run gates automatically in this phase.

JavaScript, TypeScript, and Go dependency audit tools are out of scope for the initial Security Gate. Deeper language-specific complexity analysis for JavaScript, TypeScript, and Go is also out of scope.

## Product Direction

The dashboard should now be able to answer whether a captured Pull Request state passed the configured quality policies. The answer must be based on deterministic evidence, not on the live mutable Pull Request state.

The user flow is:

```text
Pull Request context exists as a pending Analysis Run
-> user clicks Execute / Analyze
-> backend runs Gate Execution
-> Analysis Run becomes completed or error
-> dashboard shows Gate Result Snapshots and Analysis Findings
```

The UI label can now move from mock-only language to real analysis language for pending Analysis Runs. Mock Analysis Run creation should remain clearly labeled as mock where it still exists.

## Domain Model

`Gate Execution` is the act of evaluating an Analysis Run against its Repository policies and producing Gate Result Snapshots plus Analysis Findings.

`Quality Gate Config` remains the blocking policy:

- minimum total coverage;
- maximum allowed coverage drop;
- minimum changed-files coverage;
- blocking security severities;
- function length limit;
- complexity limit;
- fail-on-new-TODO behavior.

`Coverage Execution Config` is a separate repository-owned configuration that describes how to produce coverage evidence before applying the policy.

## Persistence Changes

Add a new one-to-one table:

```text
coverage_execution_configs
- id
- repository_id
- language
- install_command
- test_command
- report_path
- report_format
- created_at
- updated_at
```

`repository_id` is unique and cascades with Repository deletion.

`language` values:

```text
python
typescript
javascript
go
```

`report_format` values:

```text
cobertura_xml
lcov
go_coverprofile
```

Repository creation should create a default Coverage Execution Config alongside the existing default Quality Gate Config. The default can start as Python and must be editable by the user.

No new Analysis Run columns are required for Fases 5-7. The existing JSONB fields remain the storage for Gate Result Snapshots:

- `coverage_result_json`;
- `security_result_json`;
- `technical_debt_result_json`.

`AnalysisFinding` remains the queryable issue model for all three gates.

## Coverage Execution Config Defaults

Initial defaults by language:

```text
Python
- install_command: pip install -r requirements.txt
- test_command: pytest --cov=. --cov-report=xml:coverage.xml
- report_path: coverage.xml
- report_format: cobertura_xml

TypeScript
- install_command: npm ci
- test_command: npm test -- --coverage
- report_path: coverage/lcov.info
- report_format: lcov

JavaScript
- install_command: npm ci
- test_command: npm test -- --coverage
- report_path: coverage/lcov.info
- report_format: lcov

Go
- install_command: go mod download
- test_command: go test ./... -coverprofile=coverage.out
- report_path: coverage.out
- report_format: go_coverprofile
```

The install command is optional. If it is blank, Coverage Gate skips the install step.

## Backend Architecture

Execution stays inside the backend service layer. Routes stay thin and do not know about Git, shell commands, coverage parsing, scanners, AST parsing, or final decision rules.

The intended module shape is:

```text
app/services/analysis_service.py
  existing list/get/mock/context run helpers

app/services/analysis_execution_service.py
  owns the external Gate Execution interface
  validates pending state
  moves Analysis Run through running/completed/error
  calls runner and gates
  persists snapshots and findings
  applies final objective decision

app/services/runner_service.py
  owns temporary workspace lifecycle
  clones/checks out repository revisions
  runs commands with timeout and restricted environment
  captures stdout/stderr/exit code

app/services/gates/coverage_gate.py
  runs coverage evidence generation
  parses coverage reports
  applies coverage policy
  returns normalized coverage result and findings

app/services/gates/security_gate.py
  runs security scanners
  normalizes scanner output
  applies configured blocking severities
  returns normalized security result and findings

app/services/gates/technical_debt_gate.py
  runs deterministic technical debt checks
  returns normalized technical debt result and findings
```

Internal parsers can be split further when needed, for example `coverage_parsers/lcov.py`, but callers should not need to know parser details.

## Execution Environment

Gate commands run in the backend/local service environment for the MVP. The system does not create a dedicated container per Analysis Run.

Required mitigations:

- create a temporary workspace per Analysis Run;
- enforce command timeout;
- clean up the workspace when `KEEP_WORKDIR=false`;
- do not pass application secrets such as GitHub, OpenAI, or LangSmith tokens into repository commands;
- capture enough command metadata to diagnose operational failures;
- document that running untrusted Pull Request code without per-run isolation is an MVP risk.

Backend settings should read the existing runner environment variables:

```text
WORKDIR
COMMAND_TIMEOUT_SECONDS
KEEP_WORKDIR
```

## Analysis Run Lifecycle

Real Gate Execution runs against an existing Analysis Run:

```http
POST /api/analysis-runs/{analysis_run_id}/execute
```

Only `Run Status = pending` can be executed.

Allowed transitions:

```text
pending -> running -> completed
pending -> running -> error
```

Blocked transitions:

```text
completed -> running
error -> running
running -> running
```

Completed, errored, and already-running Analysis Runs cannot be re-executed in place. Retry semantics are out of scope and should be modeled later as an explicit new attempt.

Execution uses the Analysis Run's persisted evidence:

- repository identity;
- Pull Request number;
- head SHA;
- Pull Request Snapshot;
- Changed File Snapshot;
- diff snapshot or per-file patches.

If a dashboard action needs to analyze a live Pull Request that has no pending Analysis Run for its current head SHA, the backend must first capture Pull Request context and create or reuse the Analysis Run, then execute that run.

## Operational Error Semantics

Gate execution failures are operational errors, not quality failures.

Operational failures include:

- clone failure;
- checkout failure;
- install command failure;
- test command failure when coverage evidence cannot be produced;
- missing coverage report;
- unparseable coverage report;
- scanner binary missing;
- scanner output missing or unparseable;
- timeout;
- missing required Pull Request diff evidence.

Quality failures include:

- total coverage below configured minimum;
- coverage drop above configured maximum;
- changed-files coverage below configured minimum;
- security findings with configured blocking severities;
- new TODO/FIXME when configured to fail;
- function length above configured limit;
- Python complexity above configured limit.

If any required gate fails operationally, the Analysis Run ends with:

```text
Run Status = error
Gate Decision = null
```

Successful partial Gate Result Snapshots and Analysis Findings are still saved. The dashboard may show partial evidence, but it must not present a pass/fail quality decision when a required gate did not complete.

## Final Decision Rules

Coverage Gate, Security Gate, and Technical Debt Gate are all required for the first real Gate Execution.

If all gates complete:

```text
any gate status = fail -> Gate Decision = fail
all gate statuses = pass -> Gate Decision = pass
```

If any gate returns an operational error:

```text
Run Status = error
Gate Decision = null
```

`PASS` means all three quality pillars ran and passed their configured policies.

Fases 5-7 do not define an AI score. `score` can remain null for real Gate Execution until a later deterministic or LangChain scoring phase is specified.

## Coverage Gate

Coverage Gate supports Python, TypeScript, JavaScript, and Go.

Coverage is calculated by running the configured install and test commands twice:

```text
checkout base SHA
run install command when configured
run test command
parse base coverage report

checkout head SHA
run install command when configured
run test command
parse Pull Request coverage report
```

The base SHA comes from the Pull Request Snapshot when available. If the Analysis Run does not have enough Pull Request Snapshot evidence to identify base and head revisions, Coverage Gate returns an operational error.

Coverage Result Snapshot should include:

- `status`: `pass`, `fail`, or `error`;
- `language`;
- `report_format`;
- `base_sha`;
- `head_sha`;
- `base_coverage`;
- `pr_coverage`;
- `coverage_drop`;
- `changed_files_coverage`;
- `changed_source_files`;
- `blocking_reasons`;
- command metadata for diagnostics when useful.

Coverage policy rules:

- fail if Pull Request total coverage is below `min_total_coverage`;
- fail if coverage drop is greater than `max_coverage_drop`;
- fail if changed-files coverage is below `min_changed_files_coverage`;
- pass when all configured coverage policies pass.

### Coverage Report Formats

Python uses Cobertura-style XML from `coverage.py`.

TypeScript and JavaScript use LCOV.

Go uses native Go coverprofile.

Tool-specific JavaScript JSON formats, Go Cobertura converters, and other coverage formats are out of scope.

### Changed Files Coverage

Changed-files coverage uses the Changed File Snapshot as the list of Pull Request file changes.

Language-aware source filtering should include relevant source files and ignore non-source files. Conventional test files, docs, generated files, and vendor/dependency directories should not block changed-files coverage unless explicitly included in a future config.

When a changed source file is missing from the Pull Request coverage report, Coverage Gate counts that file as `0%` covered.

When no changed source files exist, `changed_files_coverage` is absent/null and the changed-files coverage rule does not block.

## Security Gate

Security Gate starts with generic scanners:

- Semgrep;
- detect-secrets.

Python receives additional checks:

- Bandit;
- pip-audit.

JavaScript, TypeScript, and Go dependency audit tools are deferred.

Scanner adapters must normalize tool-specific output into:

- category: `security`;
- severity: `low`, `medium`, `high`, or `critical`;
- file path when available;
- line number when available;
- title;
- description;
- scanner/tool metadata in the security snapshot when useful.

`Quality Gate Config.security_fail_on` decides blocking behavior.

Default:

```text
critical
high
```

Findings with normalized severity included in `security_fail_on` are blocking. Other security findings are non-blocking.

Security Result Snapshot should include:

- `status`: `pass`, `fail`, or `error`;
- counts by severity;
- scanners run;
- blocking reasons;
- warnings or non-blocking summaries when useful.

Scanner exit codes need careful interpretation. A scanner exit code that means "findings found" is not an operational error if parseable results are produced. Missing binaries, timeouts, and unparseable output are operational errors.

## Technical Debt Gate

Technical Debt Gate starts with deterministic rules only.

All supported languages:

- detect new TODO/FIXME markers from diff evidence.

Python:

- detect functions above `max_function_lines`;
- detect complexity above `max_complexity` using a Python complexity tool such as Radon.

TypeScript, JavaScript, and Go:

- detect functions above `max_function_lines`;
- do not enforce complexity in the first implementation.

LangChain architecture review is out of scope for Fase 7.

### New TODO/FIXME Detection

The source of truth for "new" TODO/FIXME markers is the Pull Request diff or per-file patches, not the final checked-out file state.

A TODO/FIXME marker blocks when:

- `fail_on_new_todo = true`;
- the marker appears on an added line in the diff;
- the file is relevant source code for the configured language.

Existing TODO/FIXME markers that were already present before the Pull Request do not block.

If diff and patch evidence are missing, new TODO/FIXME detection is unavailable. Because Technical Debt Gate is required in this phase, missing required diff evidence should produce an operational error instead of guessing from the final file state.

Technical Debt Result Snapshot should include:

- `status`: `pass`, `fail`, or `error`;
- count of new TODO/FIXME findings;
- count of function length findings;
- count of complexity findings when applicable;
- blocking reasons;
- suggestions when deterministic checks can produce them.

## API Changes

Add Coverage Execution Config endpoints:

```http
GET /api/repositories/{repository_id}/coverage-execution-config
PUT /api/repositories/{repository_id}/coverage-execution-config
```

The update payload should allow:

- `language`;
- `install_command`;
- `test_command`;
- `report_path`;
- `report_format`.

Add the real execution endpoint:

```http
POST /api/analysis-runs/{analysis_run_id}/execute
```

The response can return `AnalysisRunDetail` after execution completes. In this synchronous MVP, the request may take as long as the configured command timeout budget allows.

If execution is attempted for a non-pending run, return a stable Operational Error such as:

```json
{
  "detail": {
    "code": "analysis_run_not_pending",
    "message": "Only pending analysis runs can be executed."
  }
}
```

## Frontend Changes

The repository workspace should expose Coverage Execution Config separately from Quality Gate Config, either as a dedicated tab or as a clearly separated section within the configuration workspace.

The Analysis Run detail page should already be able to show interpreted pillar snapshots and Analysis Findings from Fase 4. Fases 5-7 should extend that display for real results:

- coverage command/report metadata;
- base and Pull Request coverage;
- coverage drop;
- changed-files coverage;
- scanner counts and blocking security findings;
- technical debt findings from TODO/FIXME, function length, and complexity;
- operational error states with partial snapshots.

Pull Request rows should provide a real execution action for pending runs. Stale or completed runs should not show an in-place re-execute action.

## Documentation

README and `.env.example` should explain:

- runner environment variables;
- that commands run in the backend/local service environment;
- the MVP risk of executing Pull Request code without per-run containers;
- required tooling for each supported coverage language;
- default Coverage Execution Config values;
- how to configure coverage for npm, pytest, and Go projects;
- that Semgrep and detect-secrets are generic Security Gate scanners;
- that Bandit and pip-audit are Python-specific first-pass checks.

## Testing

Backend tests should cover:

- default Coverage Execution Config creation with Repository creation;
- Coverage Execution Config read/update validation;
- rejecting execution of non-pending Analysis Runs;
- pending Analysis Run lifecycle through running and completed;
- pending Analysis Run lifecycle through running and error;
- saving partial snapshots when one gate errors;
- final decision pass when all gates pass;
- final decision fail when any completed gate fails;
- coverage base/head comparison behavior;
- missing changed source file coverage counted as zero;
- changed-files coverage absent when no changed source files exist;
- LCOV parsing for JavaScript/TypeScript;
- Cobertura XML parsing for Python;
- Go coverprofile parsing;
- security severity normalization and `security_fail_on` blocking behavior;
- scanner findings exit code treated as quality result when output is parseable;
- scanner missing/unparseable output treated as operational error;
- new TODO/FIXME detection from added diff lines only;
- old TODO/FIXME markers not blocking;
- function length checks for Python, TypeScript, JavaScript, and Go;
- Python complexity checks.

Frontend verification should cover:

- TypeScript build;
- Coverage Execution Config form;
- pending Analysis Run execution action;
- no execute action for completed, error, or running runs;
- real pillar snapshots in Analysis Run detail;
- partial snapshot display for errored runs.

## Success Criteria

Fases 5-7 are complete when:

1. a Repository owns an editable Coverage Execution Config separate from Quality Gate Config;
2. a pending Analysis Run can be executed through `/api/analysis-runs/{analysis_run_id}/execute`;
3. execution runs against the Analysis Run's persisted Pull Request evidence;
4. Coverage Gate supports Python Cobertura XML, TypeScript LCOV, JavaScript LCOV, and Go coverprofile;
5. Coverage Gate compares base and head coverage by running coverage on both revisions;
6. missing changed source files in coverage reports count as 0% coverage;
7. Security Gate runs Semgrep and detect-secrets generically, plus Bandit and pip-audit for Python;
8. security findings block according to configured normalized severity;
9. Technical Debt Gate detects new TODO/FIXME from diff evidence;
10. Technical Debt Gate checks function length across supported languages;
11. Technical Debt Gate checks Python complexity;
12. operational gate failures produce `Run Status = error` and no Gate Decision;
13. partial successful gate snapshots are saved when another required gate errors;
14. all three gates must complete before producing a pass/fail Gate Decision;
15. dashboard surfaces real gate results and operational errors clearly;
16. backend tests and frontend TypeScript build pass.

## Related Decisions

- `docs/adr/0014-support-multi-language-coverage-gate.md`
- `docs/adr/0015-use-explicit-coverage-execution-config.md`
- `docs/adr/0016-store-coverage-execution-config-separately.md`
- `docs/adr/0017-run-coverage-on-base-and-head.md`
- `docs/adr/0018-treat-gate-execution-failures-as-operational-errors.md`
- `docs/adr/0019-use-lcov-for-javascript-coverage.md`
- `docs/adr/0020-use-native-go-coverprofile.md`
- `docs/adr/0021-count-missing-changed-code-coverage-as-zero.md`
- `docs/adr/0022-start-security-gate-with-generic-scanners.md`
- `docs/adr/0023-use-configured-security-severities-for-blocking.md`
- `docs/adr/0024-start-technical-debt-gate-with-deterministic-rules.md`
- `docs/adr/0025-use-diff-as-source-for-new-todo-detection.md`
- `docs/adr/0026-save-partial-gate-results-on-execution-error.md`
- `docs/adr/0027-require-all-gates-for-final-decision.md`
- `docs/adr/0028-execute-existing-analysis-runs.md`
- `docs/adr/0029-execute-only-pending-analysis-runs.md`
- `docs/adr/0030-run-gates-in-backend-environment-for-mvp.md`
- `docs/adr/0031-add-install-command-to-coverage-execution-config.md`
