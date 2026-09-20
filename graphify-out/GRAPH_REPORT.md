# Graph Report - workspace  (2026-09-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1573 nodes · 5090 edges · 80 communities (60 shown, 20 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 546 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `827c72aa`
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
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 77
- Community 79

## God Nodes (most connected - your core abstractions)
1. `AnalysisRunStatus` - 95 edges
2. `AppError` - 86 edges
3. `AnalysisRun` - 85 edges
4. `get_settings()` - 76 edges
5. `GateDecision` - 56 edges
6. `FindingCategory` - 55 edges
7. `GitHubClient` - 51 edges
8. `AnalysisTriggerSource` - 50 edges
9. `Repository` - 50 edges
10. `Settings` - 45 edges

## Surprising Connections (you probably didn't know these)
- `test_manual_analyze_enqueues_pending_run()` --uses--> `AnalysisTriggerSource`  [INFERRED]
  backend/tests/test_manual_pr_analysis.py → backend/app/models/enums.py
- `_publish_comment()` --uses--> `GitHubClient`  [INFERRED]
  backend/app/services/github_publication_service.py → backend/app/services/github_service.py
- `_publish_commit_status()` --uses--> `GitHubClient`  [INFERRED]
  backend/app/services/github_publication_service.py → backend/app/services/github_service.py
- `GitHubClient` --uses--> `AppError`  [INFERRED]
  backend/app/services/github_service.py → backend/app/core/errors.py
- `GitHubClient` --uses--> `GitHubPullRequestRead`  [INFERRED]
  backend/app/services/github_service.py → backend/app/schemas/github.py

## Import Cycles
- None detected.

## Communities (80 total, 20 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (41): ChangedFileSnapshot, GitHubClient, _map_changed_file(), _map_pull_request(), _map_pull_request_snapshot(), Any, Response, test_map_pull_request() (+33 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (28): _create_run(), _execute(), _gate_result(), github_writes(), fake_list(), fixture, _set_publish_flags(), _stub_passing_gates() (+20 more)

### Community 2 - "Community 2"
Cohesion: 0.17
Nodes (22): get_current_user(), Request, Session, require_csrf_token(), get_install_url(), list_installations(), get, Session (+14 more)

### Community 3 - "Community 3"
Cohesion: 0.16
Nodes (39): GitHubAppInstallation, GitHubConnection, InstallationRepository, UserRepositoryAccess, User, deactivate_installation(), get_active_installation_for_repository(), _get_paginated_github_resource() (+31 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (34): app_core_config, app_core_errors, app_models_github_connection, app_models_oauth_state, app_models_user, app_services, build_login_url(), cleanup_expired_oauth_states() (+26 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (38): app_models_github_app_installation, app_models_installation_repository, app_models_repository, app_models_user_repository_access, app_models_user_session, _post_login_redirect_url(), clear_session_cookies(), create_session() (+30 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (39): AnalysisFindingRead, AnalysisRunDetail, AnalysisRunSummary, GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult, BaseModel, analysis_run_target_url() (+31 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (34): parse_cobertura_xml(), Path, parse_go_coverprofile(), Path, parse_lcov(), flush(), Path, calculate_total() (+26 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (3): alembic, collections_abc, sqlalchemy_dialects

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (22): download_repository_archive(), parse_repository_url(), redacted_command(), repository_clone_url(), RepositoryRef, _validate_archive_members(), test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths() (+14 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (23): CommandResult, run_command(), test_evidence_workspace_prepare_base_and_path_guard(), run(), test_evidence_workspace_missing_base_sha_and_reprepare_revision(), run(), test_run_revision_coverage_missing_report_and_parse_formats(), run() (+15 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (31): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+23 more)

### Community 12 - "Community 12"
Cohesion: 0.10
Nodes (26): database_health(), health(), get, Session, readiness(), app_error_handler(), AppError, Exception (+18 more)

### Community 13 - "Community 13"
Cohesion: 0.17
Nodes (29): AnalysisRunStatus, GateDecision, _FakeRun, test_dashboard_action_fail_and_skip_none_action(), test_report_service_pass_summary_and_suggestions(), _fake_analysis_run(), test_report_service_skipped_and_error_ai_review_paths(), _disable_github_publication() (+21 more)

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (29): build_graph(), compiled_review_graph(), _correct_draft(), draft(), emit(), load_evidence(), Any, retrieve() (+21 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (28): Any, model_validator, Settings, validate_runtime_security_settings(), tracing_enabled(), create_runner_workspace(), _default_runner_adapter(), RunnerWorkspace (+20 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (21): invoke_review_tools(), Invoke the four tools so LangSmith can record tool spans when tracing is on., _parse_payload(), run_forever(), test_invoke_review_tools_fallback_changed_file_without_blocking_hunks(), test_allowed_file_paths_includes_string_changed_files(), test_compiled_review_graph_is_cached(), test_coverage_gate_is_source_file_branches() (+13 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (20): CoverageExecutionConfig, CoverageLanguage, CoverageReportFormat, CoverageExecutionConfigRead, CoverageExecutionConfigUpdate, BaseModel, model_validator, build_coverage_execution_config() (+12 more)

### Community 18 - "Community 18"
Cohesion: 0.10
Nodes (25): get_coverage_execution_config(), get, put, Session, UUID, update_coverage_execution_config(), get_dashboard_summary(), get (+17 more)

### Community 19 - "Community 19"
Cohesion: 0.19
Nodes (27): FindingCategory, FindingSeverity, _blocking_severities(), build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner() (+19 more)

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (24): API_BASE_URL, ApiError, getCookieValue(), getCurrentUser(), getGitHubInstallUrl(), getGitHubLoginUrl(), getHealth(), getPullRequestContext() (+16 more)

### Community 21 - "Community 21"
Cohesion: 0.22
Nodes (27): analyze_pull_request(), post, AnalysisRun, AnalysisTriggerSource, PullRequestContextRead, _build_pending_run(), _coerce_context(), _commit_new_run_or_reuse() (+19 more)

### Community 22 - "Community 22"
Cohesion: 0.31
Nodes (13): Base, TimestampMixin, UUIDPrimaryKeyMixin, OAuthState, QualityGateConfig, UserSession, datetime, DeclarativeBase (+5 more)

### Community 23 - "Community 23"
Cohesion: 0.11
Nodes (26): getAnalysisRun(), getQualityGateConfig(), publishAnalysisRunToGitHub(), AnalysisDetailPage, AIReviewPanel(), AnalysisDetailPage(), handlePublish(), handleRetry() (+18 more)

### Community 24 - "Community 24"
Cohesion: 0.09
Nodes (22): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+14 more)

### Community 25 - "Community 25"
Cohesion: 0.10
Nodes (5): GateExecutionEvidenceWorkspace, PreparedRevision, Path, test_base_coverage_skipped_when_no_drop_policy(), test_coverage_gate_runs_commands_in_configured_working_directory()

### Community 26 - "Community 26"
Cohesion: 0.20
Nodes (23): AnalysisJob, claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), timedelta, UUID (+15 more)

### Community 27 - "Community 27"
Cohesion: 0.26
Nodes (22): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+14 more)

### Community 28 - "Community 28"
Cohesion: 0.11
Nodes (13): _docker_run_command(), IsolatedRunnerWorkspace, _make_workspace_writable(), Exception, Path, UUID, RunnerError, test_make_workspace_writable_skips_os_errors() (+5 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (18): getDashboardSummary(), DashboardPage, AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts() (+10 more)

### Community 30 - "Community 30"
Cohesion: 0.20
Nodes (19): Repository, BaseModel, model_validator, RepositoryCreate, RepositoryRead, create_repository(), get_repository(), get_repository_by_full_name() (+11 more)

### Community 31 - "Community 31"
Cohesion: 0.21
Nodes (21): DashboardBlockingCategory, DashboardFindingCount, DashboardOpenPullRequestAction, DashboardRecentAnalysisRun, DashboardSummaryRead, BaseModel, _action_for_open_pull_request(), _calculate_approval_rate() (+13 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (23): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), collect_tool_results(), get_changed_file_hunk(), get_gate_summary() (+15 more)

### Community 33 - "Community 33"
Cohesion: 0.13
Nodes (17): analyzePullRequest(), executeAnalysisRun(), listPullRequests(), RepositoryAnalysisRunsPage, RepositoryPullRequestsPage, EmptyState(), EmptyStateProps, StatusBadge() (+9 more)

### Community 34 - "Community 34"
Cohesion: 0.13
Nodes (20): app_api_deps, app_db_session, app_schemas_auth, app_services_session_service, AuthenticatedUser, get_me(), github_callback(), github_login() (+12 more)

### Community 35 - "Community 35"
Cohesion: 0.16
Nodes (10): AnalysisFinding, build_ai_review_input(), test_build_ai_review_input_redacts_diff_changed_files_and_findings(), _insert_run(), test_admin_execute_enqueues_run_and_returns_accepted(), test_get_analysis_run_detail(), test_list_analysis_runs_cache_miss_stores_repository_payload(), test_list_analysis_runs_for_repository() (+2 more)

### Community 36 - "Community 36"
Cohesion: 0.23
Nodes (18): GitHubPullRequestRead, GitHubWebhookResult, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, BaseModel, _has_valid_signature(), _ignored() (+10 more)

### Community 37 - "Community 37"
Cohesion: 0.17
Nodes (17): generate_ai_review_snapshot(), AIReviewGenerated, AIReviewSkipped, BaseModel, build_invocation_config(), Any, _load_example(), test_error_snapshot_shape_unchanged() (+9 more)

### Community 38 - "Community 38"
Cohesion: 0.21
Nodes (18): AST, analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), Path, _python_complexity(), run_technical_debt_gate() (+10 more)

### Community 39 - "Community 39"
Cohesion: 0.18
Nodes (11): _insert_analysis_run(), _patch_pull_requests(), fake_list_pull_requests(), _pull_request(), datetime, test_list_pull_requests_batches_review_state_for_multiple_prs(), test_list_pull_requests_includes_not_run_review_state(), test_list_pull_requests_marks_different_head_sha_as_outdated() (+3 more)

### Community 40 - "Community 40"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 41 - "Community 41"
Cohesion: 0.14
Nodes (13): _remove_container(), run_isolated_command(), _runner_resource_limits(), _safe_env(), test_remove_container_swallows_errors(), test_command_result_snapshot_redacts_output(), test_isolated_runner_does_not_pass_app_secrets_to_container(), test_safe_env_defaults_path_when_absent() (+5 more)

### Community 42 - "Community 42"
Cohesion: 0.12
Nodes (9): apply_coverage_policy(), test_coverage_file_percentage_when_total_zero(), test_coverage_gate_is_source_file_variants(), test_coverage_gate_parse_report_and_unmatched_warning(), test_github_client_raise_for_response_variants(), test_security_normalize_scanner_branches(), test_technical_debt_gate_python_and_brace_paths(), test_technical_debt_gate_syntax_error_returns_error() (+1 more)

### Community 43 - "Community 43"
Cohesion: 0.22
Nodes (14): get_quality_gate_config(), get, put, Session, UUID, update_quality_gate_config(), BaseModel, QualityGateConfigRead (+6 more)

### Community 44 - "Community 44"
Cohesion: 0.16
Nodes (8): Runner, load_examples(), main(), Push the git-versioned AI review golden dataset to LangSmith as qg-ai-…, pathlib, Protocol, shutil, sys

### Community 45 - "Community 45"
Cohesion: 0.33
Nodes (13): execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), Session, UUID, _run_pipeline() (+5 more)

### Community 46 - "Community 46"
Cohesion: 0.18
Nodes (12): _archive_url(), _github_archive_headers(), _NoAuthOnRedirect, test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header(), email_message, shlex, stat (+4 more)

### Community 47 - "Community 47"
Cohesion: 0.28
Nodes (11): _create_run(), _raise_installation_token_error(), _set_publish_flags(), test_publish_commit_status_maps_decision(), test_publish_creates_marked_pull_request_comment(), fake_create(), test_publish_installation_token_failure_returns_stable_error(), test_publish_redacts_pull_request_comment_body() (+3 more)

### Community 48 - "Community 48"
Cohesion: 0.23
Nodes (13): getCoverageExecutionConfig(), updateCoverageExecutionConfig(), updateQualityGateConfig(), RepositoryQualityGateConfigPage, RepositoryWorkspaceContext, coveragePreset(), RepositoryQualityGateConfigPage(), enablePullRequestPublication() (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.24
Nodes (8): _gate_result(), _insert_pending_run(), test_analysis_execution_reraises_app_error_and_missing_run(), test_analysis_execution_timeout_after_each_gate(), test_coverage_file_percentage_non_zero(), test_run_pipeline_time_budget_checks_between_gates(), timeout_after(), test_worker_main_invokes_run_forever()

### Community 50 - "Community 50"
Cohesion: 0.29
Nodes (9): logout(), App(), AuthenticatedApp(), handleLogout(), HelpPage, frontend_src_styles_app, react, react-dom (+1 more)

### Community 51 - "Community 51"
Cohesion: 0.27
Nodes (8): getRepository(), listAnalysisRuns(), RepositoryDetailPage, RunTicker(), RunTickerProps, tickClass(), RepositoryDetailPage(), AnalysisRunSummary

### Community 52 - "Community 52"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.29
Nodes (9): client(), db_session(), fixture, repository(), reset_database(), _reset_public_schema(), load_run(), fastapi_testclient (+1 more)

### Community 54 - "Community 54"
Cohesion: 0.22
Nodes (8): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, routePrefix

### Community 55 - "Community 55"
Cohesion: 0.43
Nodes (8): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get, post, Session, UUID

### Community 56 - "Community 56"
Cohesion: 0.38
Nodes (6): _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional(), pytest, skipif

### Community 57 - "Community 57"
Cohesion: 0.47
Nodes (6): _find_webhook_user(), _process_installation_event(), Any, Session, test_webhook_find_user_without_sender(), test_webhook_installation_branches()

### Community 62 - "Community 62"
Cohesion: 0.50
Nodes (4): post, Request, Session, receive_github_webhook()

### Community 68 - "Community 68"
Cohesion: 0.67
Nodes (3): installation_token(), publication_repository(), fixture

## Knowledge Gaps
- **80 isolated node(s):** `ErrorMessageProps`, `LoadingBlockProps`, `RunStatusDonutProps`, `AnalysisFinding`, `AnalysisTriggerSource` (+75 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 401 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 2` to `Community 0`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 9`, `Community 10`, `Community 12`, `Community 14`, `Community 15`, `Community 16`, `Community 18`, `Community 28`, `Community 36`, `Community 37`, `Community 41`, `Community 42`, `Community 43`, `Community 45`, `Community 46`, `Community 55`, `Community 61`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `AppError` connect `Community 12` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 36`, `Community 6`, `Community 42`, `Community 43`, `Community 45`, `Community 13`, `Community 47`, `Community 16`, `Community 17`, `Community 49`, `Community 21`, `Community 30`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `GitHubClient` connect `Community 0` to `Community 1`, `Community 36`, `Community 6`, `Community 39`, `Community 9`, `Community 42`, `Community 12`, `Community 47`, `Community 16`, `Community 49`, `Community 21`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 67 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `AnalysisRun` (e.g. with `AnalysisRunStatus` and `AnalysisTriggerSource`) actually correct?**
  _`AnalysisRun` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `get_settings()` (e.g. with `build_login_url()` and `create_oauth_state()`) actually correct?**
  _`get_settings()` has 4 INFERRED edges - model-reasoned connections that need verification._