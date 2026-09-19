# Graph Report - workspace  (2026-09-19)

## Corpus Check
- 271 files · ~111,490 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 19 file(s) not represented in the graph (top: (none) 12, .css 2, .mdc 1)

## Summary
- 1498 nodes · 4417 edges · 90 communities (66 shown, 24 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 461 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `300625ad`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- github_installation_service.py
- GitHubClient
- github_publication_service.py
- coverage_gate.py
- test_github_webhooks.py
- test_coverage_execution_config.py
- collections_abc
- test_analysis_execution.py
- package.json
- routes_repositories.py
- client.ts
- github_oauth_service.py
- test_analysis_queue.py
- test_ai_review_graph.py
- AnalysisRunStatus
- api.ts
- FindingCategory
- test_runner_secrets.py
- tools.py
- AnalysisDetailPage.tsx
- evaluators.py
- RepositoryPullRequestsPage.tsx
- graph.py
- test_github_client_context.py
- DashboardPage.tsx
- GateExecutionEvidenceWorkspace
- test_auth.py
- What You Must Do When Invoked
- test_runner_protocol.py
- compilerOptions
- What You Must Do When Invoked
- test_installation_token_is_not_persisted
- get_settings
- quality_gate_service.py
- runner_service.py
- What You Must Do When Invoked
- dashboard_service.py
- analysis_execution_service.py
- test_ai_review_evals.py
- test_repositories.py
- test_base_coverage_skipped_when_no_drop_policy
- compilerOptions
- analysis_evidence_workspace.py
- pydantic
- backend
- PR Quality Gate Dashboard
- test_github_publication.py
- frontend/vercel.json
- quality-gate-backend
- AnalysisRun
- tests/conftest.py
- App.tsx
- RunnerError
- graphify reference: extra exports and benchmark
- CLAUDE.md
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- graphify reference: query, path, explain
- test_coverage_gate_runs_commands_in_configured_working_directory
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native AGENTS.md integration
- graphify reference: incremental update and cluster-only
- env.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- _process_installation_event
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- .agents/skills/graphify/references/extraction-spec.md
- .claude/skills/graphify/references/extraction-spec.md
- .codex/skills/graphify/references/extraction-spec.md

## God Nodes (most connected - your core abstractions)
1. `AnalysisRunStatus` - 75 edges
2. `AnalysisRun` - 74 edges
3. `get_settings()` - 74 edges
4. `AppError` - 68 edges
5. `FindingCategory` - 50 edges
6. `User` - 49 edges
7. `GateDecision` - 47 edges
8. `GitHubClient` - 46 edges
9. `AnalysisTriggerSource` - 38 edges
10. `Repository` - 36 edges

## Surprising Connections (you probably didn't know these)
- `Commands` --references--> `reset_database()`  [INFERRED]
  CLAUDE.md → backend/tests/conftest.py
- `Architecture` --references--> `get_settings()`  [INFERRED]
  CLAUDE.md → backend/app/core/config.py
- `Architecture` --references--> `Settings`  [INFERRED]
  CLAUDE.md → backend/app/core/config.py
- `Architecture` --references--> `AppError`  [INFERRED]
  CLAUDE.md → backend/app/core/errors.py
- `Architecture` --references--> `Base`  [INFERRED]
  CLAUDE.md → backend/app/db/base.py

## Import Cycles
- None detected.

## Communities (90 total, 24 thin omitted)

### Community 0 - "github_installation_service.py"
Cohesion: 0.15
Nodes (39): Base, GitHubAppInstallation, GitHubConnection, InstallationRepository, TimestampMixin, UUIDPrimaryKeyMixin, QualityGateConfig, Repository (+31 more)

### Community 1 - "GitHubClient"
Cohesion: 0.07
Nodes (58): post, Request, Session, receive_github_webhook(), analyze_pull_request(), post, ChangedFileSnapshot, GitHubPullRequestRead (+50 more)

### Community 2 - "github_publication_service.py"
Cohesion: 0.31
Nodes (17): GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult, BaseModel, analysis_run_target_url(), _client_for_run(), _get_run(), publish_analysis_run_to_github() (+9 more)

### Community 3 - "coverage_gate.py"
Cohesion: 0.12
Nodes (36): parse_cobertura_xml(), Path, parse_go_coverprofile(), Path, parse_lcov(), flush(), Path, calculate_total() (+28 more)

### Community 4 - "test_github_webhooks.py"
Cohesion: 0.16
Nodes (22): _patch_context(), fake_context(), _post_webhook(), _pull_request_context(), _pull_request_payload(), fixture, _signed_headers(), test_installation_webhook_dispatches_sync() (+14 more)

### Community 5 - "test_coverage_execution_config.py"
Cohesion: 0.10
Nodes (17): CoverageExecutionConfig, CoverageLanguage, CoverageExecutionConfigUpdate, BaseModel, model_validator, build_coverage_execution_config(), get_coverage_execution_config(), map_github_language() (+9 more)

### Community 6 - "collections_abc"
Cohesion: 0.07
Nodes (3): alembic, collections_abc, sqlalchemy_dialects

### Community 7 - "test_analysis_execution.py"
Cohesion: 0.05
Nodes (62): AST, is_source_file(), _blocking_severities(), build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner() (+54 more)

### Community 8 - "package.json"
Cohesion: 0.06
Nodes (31): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+23 more)

### Community 9 - "routes_repositories.py"
Cohesion: 0.12
Nodes (36): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get, post, Session, UUID (+28 more)

### Community 10 - "client.ts"
Cohesion: 0.15
Nodes (26): analyzePullRequest(), ApiError, getCookieValue(), getCoverageExecutionConfig(), getGitHubInstallUrl(), getHealth(), getPullRequestContext(), getQualityGateConfig() (+18 more)

### Community 11 - "github_oauth_service.py"
Cohesion: 0.17
Nodes (21): OAuthState, cleanup_expired_oauth_states(), consume_oauth_state(), create_oauth_state(), CreatedOAuthState, exchange_code_for_user(), _hash_oauth_value(), Session (+13 more)

### Community 12 - "test_analysis_queue.py"
Cohesion: 0.16
Nodes (26): AnalysisJob, claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), timedelta, UUID (+18 more)

### Community 13 - "test_ai_review_graph.py"
Cohesion: 0.12
Nodes (26): Any, model_validator, Settings, compiled_review_graph(), generate_ai_review_snapshot(), AIReviewError, AIReviewGenerated, AIReviewSkipped (+18 more)

### Community 14 - "AnalysisRunStatus"
Cohesion: 0.24
Nodes (22): AnalysisRunStatus, GateDecision, _disable_github_publication(), _enable_github_publication(), _insert_run(), _open_pull_request(), _patch_open_pull_requests(), _set_github_publication() (+14 more)

### Community 15 - "api.ts"
Cohesion: 0.09
Nodes (25): chartColors, FindingsBar(), SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonut(), RunStatusDonutProps, STATUS_COLOR, ScoreSparkline() (+17 more)

### Community 16 - "FindingCategory"
Cohesion: 0.16
Nodes (19): AnalysisFinding, AnalysisTriggerSource, CoverageReportFormat, FindingCategory, FindingSeverity, AnalysisFindingRead, AnalysisRunDetail, AnalysisRunSummary (+11 more)

### Community 17 - "test_runner_secrets.py"
Cohesion: 0.18
Nodes (13): _docker_run_command(), _remove_container(), run_isolated_command(), _runner_resource_limits(), _safe_env(), test_command_result_snapshot_redacts_output(), test_isolated_runner_does_not_pass_app_secrets_to_container(), test_redact_text_leaves_plain_text_untouched() (+5 more)

### Community 18 - "tools.py"
Cohesion: 0.15
Nodes (24): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), ChangedFileHunkArgs, collect_tool_results(), get_changed_file_hunk() (+16 more)

### Community 19 - "AnalysisDetailPage.tsx"
Cohesion: 0.09
Nodes (33): Architecture, executeAnalysisRun(), getAnalysisRun(), getRepository(), listAnalysisRuns(), publishAnalysisRunToGitHub(), AIReviewPanel(), AnalysisDetailPage() (+25 more)

### Community 20 - "evaluators.py"
Cohesion: 0.28
Nodes (21): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+13 more)

### Community 21 - "RepositoryPullRequestsPage.tsx"
Cohesion: 0.16
Nodes (17): EmptyState(), EmptyStateProps, ErrorMessage(), ErrorMessageProps, LoadingBlock(), LoadingBlockProps, RunTicker(), RunTickerProps (+9 more)

### Community 22 - "graph.py"
Cohesion: 0.19
Nodes (20): build_graph(), _correct_draft(), draft(), emit(), load_evidence(), Any, retrieve(), validate() (+12 more)

### Community 23 - "test_github_client_context.py"
Cohesion: 0.14
Nodes (15): parse_repository_url(), repository_clone_url(), RepositoryRef, _github_archive(), _github_response(), test_command_snapshot_redacts_clone_token(), test_download_repository_archive_extracts_checkout_without_git(), test_github_client_uses_provided_installation_token() (+7 more)

### Community 24 - "DashboardPage.tsx"
Cohesion: 0.15
Nodes (18): getDashboardSummary(), AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts(), deriveInsights() (+10 more)

### Community 25 - "GateExecutionEvidenceWorkspace"
Cohesion: 0.20
Nodes (3): GateExecutionEvidenceWorkspace, PreparedRevision, Path

### Community 26 - "test_auth.py"
Cohesion: 0.09
Nodes (48): get_me(), github_callback(), github_login(), logout(), _post_login_redirect_url(), get, post, Request (+40 more)

### Community 27 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 28 - "test_runner_protocol.py"
Cohesion: 0.16
Nodes (9): create_runner_workspace(), _default_runner_adapter(), IsolatedRunnerWorkspace, UUID, RunnerWorkspace, test_production_defaults_to_isolated_runner_adapter(), test_production_rejects_local_runner_without_override(), test_runner_workspace_satisfies_runner_protocol() (+1 more)

### Community 29 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 30 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 32 - "get_settings"
Cohesion: 0.13
Nodes (32): get_current_user(), Request, Session, require_csrf_token(), get_install_url(), database_health(), health(), get (+24 more)

### Community 33 - "quality_gate_service.py"
Cohesion: 0.24
Nodes (13): get_quality_gate_config(), get, put, Session, UUID, update_quality_gate_config(), BaseModel, QualityGateConfigRead (+5 more)

### Community 34 - "runner_service.py"
Cohesion: 0.18
Nodes (12): _archive_url(), _NoAuthOnRedirect, test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header(), email_message, shlex, shutil, stat (+4 more)

### Community 35 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 36 - "dashboard_service.py"
Cohesion: 0.23
Nodes (20): DashboardBlockingCategory, DashboardFindingCount, DashboardOpenPullRequestAction, DashboardRecentAnalysisRun, DashboardSummaryRead, BaseModel, _action_for_open_pull_request(), _calculate_approval_rate() (+12 more)

### Community 37 - "analysis_execution_service.py"
Cohesion: 0.42
Nodes (9): execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), Session, UUID, _run_pipeline() (+1 more)

### Community 38 - "test_ai_review_evals.py"
Cohesion: 0.23
Nodes (10): load_examples(), main(), Push the git-versioned AI review golden dataset to LangSmith as qg-ai-…, _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional(), json (+2 more)

### Community 39 - "test_repositories.py"
Cohesion: 0.18
Nodes (11): _insert_analysis_run(), _patch_pull_requests(), fake_list_pull_requests(), _pull_request(), datetime, test_list_pull_requests_batches_review_state_for_multiple_prs(), test_list_pull_requests_includes_not_run_review_state(), test_list_pull_requests_marks_different_head_sha_as_outdated() (+3 more)

### Community 41 - "compilerOptions"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 42 - "analysis_evidence_workspace.py"
Cohesion: 0.25
Nodes (4): Runner, CommandResult, redacted_command(), Protocol

### Community 43 - "pydantic"
Cohesion: 0.17
Nodes (10): list_installations(), get, Session, CurrentUserRead, BaseModel, CoverageExecutionConfigRead, GitHubInstallationRead, GitHubInstallUrlRead (+2 more)

### Community 44 - "backend"
Cohesion: 0.22
Nodes (8): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, routePrefix

### Community 45 - "PR Quality Gate Dashboard"
Cohesion: 0.10
Nodes (18): CI, First-time setup (developer), Graphify, Graphify Cloud and GitHub PR reviews, Prerequisites, Project layout, Relationship to Quality Gate, AI Review (+10 more)

### Community 49 - "test_github_publication.py"
Cohesion: 0.23
Nodes (13): _create_run(), installation_token(), fixture, _raise_installation_token_error(), _set_publish_flags(), test_publish_commit_status_maps_decision(), test_publish_creates_marked_pull_request_comment(), fake_create() (+5 more)

### Community 57 - "AnalysisRun"
Cohesion: 0.33
Nodes (14): AnalysisRun, _blocking_reasons(), build_final_report(), build_github_comment_body(), build_operational_error_report(), _list_section(), _pillar_section(), _snapshot_summary() (+6 more)

### Community 58 - "tests/conftest.py"
Cohesion: 0.21
Nodes (12): client(), create_user_repo_access(), create(), db_session(), fixture, repository(), reset_database(), _reset_public_schema() (+4 more)

### Community 59 - "App.tsx"
Cohesion: 0.22
Nodes (11): getCurrentUser(), getGitHubLoginUrl(), logout(), App(), AuthenticatedApp(), handleLogout(), AuthGate(), HelpPage() (+3 more)

### Community 60 - "RunnerError"
Cohesion: 0.23
Nodes (9): download_repository_archive(), _github_archive_headers(), _make_workspace_writable(), Exception, Path, run_command(), RunnerError, _validate_archive_members() (+1 more)

### Community 61 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 62 - "CLAUDE.md"
Cohesion: 0.19
Nodes (4): test_user_installation_resource_paginates_with_oauth_token(), Conventions, graphify, Project

### Community 63 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 64 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 65 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 67 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 68 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 69 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 70 - "graphify reference: commit hook and native AGENTS.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### Community 71 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 73 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 74 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 75 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 76 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 77 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 78 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 81 - "_process_installation_event"
Cohesion: 1.00
Nodes (3): _find_webhook_user(), _process_installation_event(), Session

## Knowledge Gaps
- **223 isolated node(s):** `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)`, `Step 1 - Ensure graphify is installed`, `Step 2 - Detect files` (+218 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 486 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture` connect `AnalysisDetailPage.tsx` to `get_settings`, `github_installation_service.py`, `GitHubClient`, `client.ts`, `test_ai_review_graph.py`, `AnalysisRunStatus`, `RepositoryPullRequestsPage.tsx`, `DashboardPage.tsx`, `AnalysisRun`, `test_auth.py`, `CLAUDE.md`?**
  _High betweenness centrality (0.199) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `get_settings` to `github_installation_service.py`, `quality_gate_service.py`, `github_publication_service.py`, `GitHubClient`, `runner_service.py`, `analysis_execution_service.py`, `test_github_webhooks.py`, `env.py`, `routes_repositories.py`, `github_oauth_service.py`, `test_analysis_queue.py`, `test_ai_review_graph.py`, `RunnerError`, `test_runner_secrets.py`, `AnalysisDetailPage.tsx`, `graph.py`, `test_auth.py`, `test_runner_protocol.py`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Why does `AnalysisRunStatus` connect `AnalysisRunStatus` to `GitHubClient`, `github_publication_service.py`, `dashboard_service.py`, `analysis_execution_service.py`, `test_github_webhooks.py`, `test_analysis_execution.py`, `test_repositories.py`, `routes_repositories.py`, `test_analysis_queue.py`, `test_ai_review_graph.py`, `FindingCategory`, `test_github_publication.py`, `AnalysisDetailPage.tsx`, `AnalysisRun`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 50 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 40 inferred relationships involving `AnalysisRun` (e.g. with `AnalysisRunStatus` and `AnalysisTriggerSource`) actually correct?**
  _`AnalysisRun` has 40 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `FindingCategory` (e.g. with `AnalysisFinding` and `AnalysisFindingRead`) actually correct?**
  _`FindingCategory` has 32 INFERRED edges - model-reasoned connections that need verification._