# Graph Report - workspace  (2026-09-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1289 nodes · 4214 edges · 57 communities (45 shown, 12 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 437 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `053524df`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 49
- Community 50
- Community 56

## God Nodes (most connected - your core abstractions)
1. `AnalysisRunStatus` - 74 edges
2. `AnalysisRun` - 73 edges
3. `get_settings()` - 73 edges
4. `AppError` - 67 edges
5. `FindingCategory` - 50 edges
6. `User` - 48 edges
7. `GateDecision` - 46 edges
8. `GitHubClient` - 45 edges
9. `AnalysisTriggerSource` - 38 edges
10. `Repository` - 36 edges

## Surprising Connections (you probably didn't know these)
- `list_installations()` --uses--> `GitHubAppInstallation`  [INFERRED]
  backend/app/api/routes_github_installations.py → backend/app/models/github_app_installation.py
- `require_repository_access()` --uses--> `GitHubAppInstallation`  [INFERRED]
  backend/app/services/github_installation_service.py → backend/app/models/github_app_installation.py
- `get_quality_gate_config()` --uses--> `QualityGateConfig`  [INFERRED]
  backend/app/services/quality_gate_service.py → backend/app/models/quality_gate_config.py
- `update_quality_gate_config()` --uses--> `QualityGateConfig`  [INFERRED]
  backend/app/services/quality_gate_service.py → backend/app/models/quality_gate_config.py
- `_set_publish_flags()` --uses--> `QualityGateConfig`  [INFERRED]
  backend/tests/test_analysis_execution.py → backend/app/models/quality_gate_config.py

## Import Cycles
- None detected.

## Communities (57 total, 12 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (97): _post_login_redirect_url(), Base, GitHubAppInstallation, GitHubConnection, InstallationRepository, TimestampMixin, UUIDPrimaryKeyMixin, QualityGateConfig (+89 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (55): ChangedFileSnapshot, GitHubPullRequestRead, GitHubPullRequestWithReviewState, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, BaseModel, get_repository_pull_request_context() (+47 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (48): AnalysisRun, GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult, BaseModel, PullRequestContextRead, _build_pending_run(), _coerce_context() (+40 more)

### Community 3 - "Community 3"
Cohesion: 0.12
Nodes (36): parse_cobertura_xml(), Path, parse_go_coverprofile(), Path, parse_lcov(), flush(), Path, calculate_total() (+28 more)

### Community 4 - "Community 4"
Cohesion: 0.10
Nodes (38): post, Request, Session, receive_github_webhook(), GitHubWebhookResult, _find_webhook_user(), _has_valid_signature(), _ignored() (+30 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (22): put, Session, update_coverage_execution_config(), CoverageExecutionConfig, CoverageLanguage, CoverageReportFormat, CoverageExecutionConfigRead, CoverageExecutionConfigUpdate (+14 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (3): alembic, collections_abc, sqlalchemy_dialects

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (24): _create_run(), _execute(), _gate_result(), _set_publish_flags(), _stub_passing_gates(), test_disabled_publication_flags_skip_github_writes(), test_execute_aborts_when_total_time_budget_exceeded(), test_execute_marks_error_on_unexpected_exception() (+16 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (32): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+24 more)

### Community 9 - "Community 9"
Cohesion: 0.15
Nodes (32): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get, post, Session, UUID (+24 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (27): ApiError, getCookieValue(), getCurrentUser(), getGitHubInstallUrl(), getGitHubLoginUrl(), getHealth(), getPullRequestContext(), listGitHubInstallations() (+19 more)

### Community 11 - "Community 11"
Cohesion: 0.13
Nodes (28): app_error_handler(), AppError, Exception, Request, OAuthState, build_login_url(), cleanup_expired_oauth_states(), consume_oauth_state() (+20 more)

### Community 12 - "Community 12"
Cohesion: 0.16
Nodes (26): AnalysisJob, claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), timedelta, UUID (+18 more)

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (21): Settings, validate_runtime_security_settings(), compiled_review_graph(), generate_ai_review_snapshot(), AIReviewError, AIReviewSkipped, BaseModel, build_invocation_config() (+13 more)

### Community 14 - "Community 14"
Cohesion: 0.22
Nodes (23): AnalysisRunStatus, GateDecision, _FakeRun, _disable_github_publication(), _enable_github_publication(), _insert_run(), _open_pull_request(), _patch_open_pull_requests() (+15 more)

### Community 15 - "Community 15"
Cohesion: 0.10
Nodes (23): chartColors, FindingsBar(), SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonut(), RunStatusDonutProps, STATUS_COLOR, ScoreSparkline() (+15 more)

### Community 16 - "Community 16"
Cohesion: 0.18
Nodes (17): AnalysisFinding, AnalysisTriggerSource, FindingCategory, FindingSeverity, AnalysisFindingRead, AnalysisRunSummary, test_build_ai_review_input_redacts_diff_changed_files_and_findings(), _insert_run() (+9 more)

### Community 17 - "Community 17"
Cohesion: 0.13
Nodes (18): redact_text(), CommandResult, _docker_run_command(), Path, redacted_command(), _remove_container(), run_command(), run_isolated_command() (+10 more)

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (24): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), ChangedFileHunkArgs, collect_tool_results(), get_changed_file_hunk() (+16 more)

### Community 19 - "Community 19"
Cohesion: 0.15
Nodes (21): getAnalysisRun(), getQualityGateConfig(), publishAnalysisRunToGitHub(), AIReviewPanel(), AnalysisDetailPage(), handlePublish(), arrayValue(), displayValue() (+13 more)

### Community 20 - "Community 20"
Cohesion: 0.26
Nodes (22): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+14 more)

### Community 21 - "Community 21"
Cohesion: 0.16
Nodes (18): executeAnalysisRun(), getRepository(), listAnalysisRuns(), LoadingBlock(), LoadingBlockProps, RunTicker(), RunTickerProps, tickClass() (+10 more)

### Community 22 - "Community 22"
Cohesion: 0.20
Nodes (18): build_graph(), _correct_draft(), draft(), emit(), load_evidence(), Any, retrieve(), validate() (+10 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (18): download_repository_archive(), _github_archive_headers(), parse_repository_url(), repository_clone_url(), RepositoryRef, _validate_archive_members(), _github_archive(), _github_response() (+10 more)

### Community 24 - "Community 24"
Cohesion: 0.15
Nodes (18): getDashboardSummary(), AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts(), deriveInsights() (+10 more)

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (4): GateExecutionEvidenceWorkspace, PreparedRevision, Path, test_coverage_gate_runs_commands_in_configured_working_directory()

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (19): get_current_user(), Request, Session, require_csrf_token(), clear_session_cookies(), CreatedSession, _decode_session(), get_user_for_session() (+11 more)

### Community 27 - "Community 27"
Cohesion: 0.22
Nodes (17): AST, is_source_file(), analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), Path, _python_complexity() (+9 more)

### Community 28 - "Community 28"
Cohesion: 0.17
Nodes (10): create_runner_workspace(), IsolatedRunnerWorkspace, _make_workspace_writable(), Exception, UUID, RunnerError, RunnerWorkspace, test_production_defaults_to_isolated_runner_adapter() (+2 more)

### Community 29 - "Community 29"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 30 - "Community 30"
Cohesion: 0.31
Nodes (16): _blocking_severities(), build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner(), normalize_semgrep(), _normalize_severity() (+8 more)

### Community 31 - "Community 31"
Cohesion: 0.18
Nodes (12): database_health(), health(), get, Session, readiness(), get_settings(), generate_app_jwt(), generate_installation_token() (+4 more)

### Community 32 - "Community 32"
Cohesion: 0.33
Nodes (5): get_db(), Session, fastapi, fastapi_middleware_cors, pydantic_settings

### Community 33 - "Community 33"
Cohesion: 0.27
Nodes (13): get_quality_gate_config(), get, put, Session, UUID, update_quality_gate_config(), BaseModel, QualityGateConfigRead (+5 more)

### Community 34 - "Community 34"
Cohesion: 0.17
Nodes (13): _archive_url(), _default_runner_adapter(), _NoAuthOnRedirect, test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header(), email_message, shlex, stat (+5 more)

### Community 35 - "Community 35"
Cohesion: 0.20
Nodes (13): get_me(), github_callback(), github_login(), logout(), get, post, Request, Response (+5 more)

### Community 36 - "Community 36"
Cohesion: 0.20
Nodes (10): analyzePullRequest(), listPullRequests(), EmptyState(), EmptyStateProps, RepositoryWorkspaceContext, PullRequestTable(), RepositoryPullRequestsPage(), analyze() (+2 more)

### Community 37 - "Community 37"
Cohesion: 0.40
Nodes (10): execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), Session, UUID, _run_pipeline() (+2 more)

### Community 38 - "Community 38"
Cohesion: 0.21
Nodes (10): load_examples(), main(), Push the git-versioned AI review golden dataset to LangSmith as qg-ai-…, _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional(), json (+2 more)

### Community 39 - "Community 39"
Cohesion: 0.29
Nodes (11): getCoverageExecutionConfig(), updateCoverageExecutionConfig(), updateQualityGateConfig(), coveragePreset(), RepositoryQualityGateConfigPage(), enablePullRequestPublication(), handleConfigSubmit(), handleCoverageExecutionSubmit() (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 42 - "Community 42"
Cohesion: 0.22
Nodes (4): Runner, hashlib, Protocol, shutil

### Community 43 - "Community 43"
Cohesion: 0.39
Nodes (7): get_install_url(), list_installations(), get, Session, GitHubInstallationRead, GitHubInstallUrlRead, BaseModel

### Community 44 - "Community 44"
Cohesion: 0.22
Nodes (8): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, routePrefix

### Community 45 - "Community 45"
Cohesion: 0.60
Nodes (6): AIReviewGenerated, _load_example(), test_graph_fail_coverage_passes_decision_lock_and_must_cite(), fake_draft(), test_graph_validation_failure_returns_ai_review_error(), fake_draft()

## Knowledge Gaps
- **80 isolated node(s):** `ErrorMessageProps`, `RunStatusDonutProps`, `AnalysisFinding`, `AnalysisTriggerSource`, `ChangedFileSnapshot` (+75 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 314 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 31` to `Community 0`, `Community 32`, `Community 33`, `Community 2`, `Community 1`, `Community 37`, `Community 4`, `Community 34`, `Community 9`, `Community 43`, `Community 11`, `Community 13`, `Community 12`, `Community 17`, `Community 22`, `Community 23`, `Community 26`, `Community 28`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `AnalysisRun` connect `Community 2` to `Community 0`, `Community 1`, `Community 37`, `Community 7`, `Community 42`, `Community 12`, `Community 13`, `Community 14`, `Community 16`, `Community 22`, `Community 25`, `Community 28`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `AppError` connect `Community 11` to `Community 32`, `Community 0`, `Community 2`, `Community 1`, `Community 4`, `Community 37`, `Community 5`, `Community 33`, `Community 7`, `Community 9`, `Community 43`, `Community 14`, `Community 26`, `Community 31`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `AnalysisRun` (e.g. with `AnalysisRunStatus` and `AnalysisTriggerSource`) actually correct?**
  _`AnalysisRun` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `FindingCategory` (e.g. with `AnalysisFinding` and `AnalysisFindingRead`) actually correct?**
  _`FindingCategory` has 32 INFERRED edges - model-reasoned connections that need verification._