# Graph Report - workspace  (2026-09-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1574 nodes · 5092 edges · 89 communities (67 shown, 22 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 548 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0daa5045`
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
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 78
- Community 79
- Community 80
- Community 81
- Community 86
- Community 88

## God Nodes (most connected - your core abstractions)
1. `AnalysisRunStatus` - 95 edges
2. `AppError` - 87 edges
3. `AnalysisRun` - 85 edges
4. `get_settings()` - 77 edges
5. `GateDecision` - 56 edges
6. `FindingCategory` - 55 edges
7. `GitHubClient` - 51 edges
8. `Repository` - 50 edges
9. `AnalysisTriggerSource` - 50 edges
10. `Settings` - 45 edges

## Surprising Connections (you probably didn't know these)
- `test_manual_analyze_enqueues_pending_run()` --uses--> `AnalysisTriggerSource`  [INFERRED]
  backend/tests/test_manual_pr_analysis.py → backend/app/models/enums.py
- `test_coverage_file_percentage_when_total_zero()` --calls--> `CoverageFile`  [EXTRACTED]
  backend/tests/test_coverage_final.py → backend/app/services/coverage_parsers/types.py
- `test_coverage_file_percentage_non_zero()` --calls--> `CoverageFile`  [EXTRACTED]
  backend/tests/test_coverage_gaps.py → backend/app/services/coverage_parsers/types.py
- `configure_langsmith_from_settings()` --uses--> `Settings`  [INFERRED]
  backend/app/services/agent/tracing.py → backend/app/core/config.py
- `get_install_url()` --uses--> `AppError`  [INFERRED]
  backend/app/api/routes_github_installations.py → backend/app/core/errors.py

## Import Cycles
- None detected.

## Communities (89 total, 22 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (43): parse_cobertura_xml(), Path, parse_go_coverprofile(), Path, parse_lcov(), flush(), Path, calculate_total() (+35 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (28): Any, model_validator, Settings, validate_runtime_security_settings(), tracing_enabled(), test_production_rejects_default_session_secret(), _fake_analysis_run(), test_allowed_file_paths_includes_string_changed_files() (+20 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (3): alembic, collections_abc, sqlalchemy_dialects

### Community 3 - "Community 3"
Cohesion: 0.17
Nodes (34): GitHubAppInstallation, GitHubConnection, InstallationRepository, UserRepositoryAccess, User, deactivate_installation(), get_active_installation_for_repository(), _get_paginated_github_resource() (+26 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (22): download_repository_archive(), parse_repository_url(), repository_clone_url(), RepositoryRef, test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths(), _github_archive(), _github_response() (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (23): CommandResult, test_evidence_workspace_prepare_base_and_path_guard(), run(), test_runner_workspace_removes_existing_root(), test_evidence_workspace_missing_base_sha_and_reprepare_revision(), run(), test_isolated_runner_workspace_paths(), test_run_revision_coverage_missing_report_and_parse_formats() (+15 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (31): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+23 more)

### Community 7 - "Community 7"
Cohesion: 0.25
Nodes (13): Base, TimestampMixin, UUIDPrimaryKeyMixin, OAuthState, UserSession, datetime, DeclarativeBase, logging_config (+5 more)

### Community 8 - "Community 8"
Cohesion: 0.14
Nodes (27): AnalysisJob, claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), timedelta, UUID (+19 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (21): CoverageExecutionConfig, CoverageLanguage, CoverageReportFormat, CoverageExecutionConfigRead, CoverageExecutionConfigUpdate, BaseModel, model_validator, build_coverage_execution_config() (+13 more)

### Community 10 - "Community 10"
Cohesion: 0.10
Nodes (24): database_health(), health(), get, Session, readiness(), get_settings(), AppError, Exception (+16 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (20): _docker_run_command(), Exception, Path, run_command(), run_isolated_command(), RunnerError, RunnerWorkspace, _validate_archive_members() (+12 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (24): API_BASE_URL, ApiError, getCookieValue(), getCurrentUser(), getGitHubInstallUrl(), getGitHubLoginUrl(), getHealth(), getPullRequestContext() (+16 more)

### Community 13 - "Community 13"
Cohesion: 0.19
Nodes (15): get_current_user(), Request, Session, require_csrf_token(), app_error_handler(), Request, get_db(), Session (+7 more)

### Community 14 - "Community 14"
Cohesion: 0.21
Nodes (26): FindingCategory, FindingSeverity, _blocking_severities(), build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner() (+18 more)

### Community 15 - "Community 15"
Cohesion: 0.20
Nodes (25): AnalysisRunStatus, GateDecision, _FakeRun, test_report_service_pass_summary_and_suggestions(), test_report_service_skipped_and_error_ai_review_paths(), _disable_github_publication(), _enable_github_publication(), _insert_run() (+17 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (25): QualityGateConfig, Repository, BaseModel, model_validator, RepositoryCreate, _upsert_repository(), create_repository(), get_repository_by_full_name() (+17 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (29): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), ChangedFileHunkArgs, collect_tool_results(), get_changed_file_hunk() (+21 more)

### Community 18 - "Community 18"
Cohesion: 0.11
Nodes (26): getAnalysisRun(), getQualityGateConfig(), publishAnalysisRunToGitHub(), AnalysisDetailPage, AIReviewPanel(), AnalysisDetailPage(), handlePublish(), handleRetry() (+18 more)

### Community 19 - "Community 19"
Cohesion: 0.09
Nodes (22): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+14 more)

### Community 20 - "Community 20"
Cohesion: 0.17
Nodes (28): get_coverage_execution_config(), get, put, Session, UUID, update_coverage_execution_config(), get_dashboard_summary(), get (+20 more)

### Community 21 - "Community 21"
Cohesion: 0.19
Nodes (23): GateResult, _create_run(), _execute(), _gate_result(), _set_publish_flags(), _stub_passing_gates(), test_disabled_publication_flags_skip_github_writes(), test_execute_aborts_when_total_time_budget_exceeded() (+15 more)

### Community 22 - "Community 22"
Cohesion: 0.17
Nodes (22): build_graph(), _correct_draft(), draft(), emit(), load_evidence(), Any, retrieve(), validate() (+14 more)

### Community 23 - "Community 23"
Cohesion: 0.15
Nodes (26): clear_session_cookies(), create_session(), CreatedSession, _decode_session(), get_user_for_session(), _hash_token(), Response, Session (+18 more)

### Community 24 - "Community 24"
Cohesion: 0.15
Nodes (21): AST, analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), Path, _python_complexity(), run_technical_debt_gate() (+13 more)

### Community 25 - "Community 25"
Cohesion: 0.23
Nodes (23): AnalysisRun, AnalysisFindingRead, AnalysisRunDetail, AnalysisRunSummary, GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult, BaseModel (+15 more)

### Community 26 - "Community 26"
Cohesion: 0.19
Nodes (23): DashboardBlockingCategory, DashboardFindingCount, DashboardOpenPullRequestAction, DashboardRecentAnalysisRun, DashboardSummaryRead, BaseModel, _action_for_open_pull_request(), _calculate_approval_rate() (+15 more)

### Community 27 - "Community 27"
Cohesion: 0.18
Nodes (21): GitHubPullRequestRead, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, BaseModel, _map_pull_request(), get_pull_request_review_state(), get_pull_request_review_states() (+13 more)

### Community 28 - "Community 28"
Cohesion: 0.26
Nodes (22): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+14 more)

### Community 29 - "Community 29"
Cohesion: 0.17
Nodes (21): _patch_context(), fake_context(), _post_webhook(), _pull_request_context(), _pull_request_payload(), fixture, _signed_headers(), test_installation_webhook_dispatches_sync() (+13 more)

### Community 30 - "Community 30"
Cohesion: 0.14
Nodes (18): getDashboardSummary(), DashboardPage, AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts() (+10 more)

### Community 31 - "Community 31"
Cohesion: 0.21
Nodes (8): ChangedFileSnapshot, GitHubClient, _map_changed_file(), _map_pull_request_snapshot(), Any, Response, test_github_client_raise_for_response_variants(), test_create_commit_status_uses_statuses_api_not_checks()

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (17): analyzePullRequest(), executeAnalysisRun(), listPullRequests(), RepositoryAnalysisRunsPage, RepositoryPullRequestsPage, EmptyState(), EmptyStateProps, StatusBadge() (+9 more)

### Community 33 - "Community 33"
Cohesion: 0.31
Nodes (19): AnalysisTriggerSource, PullRequestContextRead, _build_pending_run(), _coerce_context(), _commit_new_run_or_reuse(), _create_or_reuse(), create_or_reuse_error_webhook_analysis_run(), create_or_reuse_manual_analysis_run() (+11 more)

### Community 34 - "Community 34"
Cohesion: 0.13
Nodes (11): Runner, create_runner_workspace(), IsolatedRunnerWorkspace, UUID, test_production_defaults_to_isolated_runner_adapter(), test_production_rejects_local_runner_without_override(), test_runner_workspace_satisfies_runner_protocol(), test_create_runner_workspace_local_in_development() (+3 more)

### Community 35 - "Community 35"
Cohesion: 0.13
Nodes (4): GateExecutionEvidenceWorkspace, PreparedRevision, Path, test_base_coverage_skipped_when_no_drop_policy()

### Community 36 - "Community 36"
Cohesion: 0.19
Nodes (15): compiled_review_graph(), generate_ai_review_snapshot(), AIReviewError, AIReviewSkipped, BaseModel, build_invocation_config(), configure_langsmith_from_settings(), Any (+7 more)

### Community 37 - "Community 37"
Cohesion: 0.18
Nodes (17): analysis_run_target_url(), publication_frontend_origin(), _create_run(), installation_token(), fixture, _raise_installation_token_error(), _set_publish_flags(), test_analysis_run_target_url_uses_frontend_origin_locally() (+9 more)

### Community 38 - "Community 38"
Cohesion: 0.13
Nodes (18): app_api_deps, app_db_session, app_schemas_auth, app_services_session_service, AuthenticatedUser, get_me(), github_callback(), github_login() (+10 more)

### Community 39 - "Community 39"
Cohesion: 0.17
Nodes (15): build_ai_review_input(), Any, redact_json_like(), redact_text(), _safe_env(), test_redact_json_like_redacts_nested_patch_without_mutating_input(), test_redact_text_masks_github_tokens_private_keys_and_assignments(), test_command_result_snapshot_redacts_output() (+7 more)

### Community 40 - "Community 40"
Cohesion: 0.16
Nodes (17): cleanup_expired_oauth_states(), consume_oauth_state(), create_oauth_state(), CreatedOAuthState, exchange_code_for_user(), _hash_oauth_value(), _oauth_state_is_valid(), Session (+9 more)

### Community 41 - "Community 41"
Cohesion: 0.18
Nodes (11): _insert_analysis_run(), _patch_pull_requests(), fake_list_pull_requests(), _pull_request(), datetime, test_list_pull_requests_batches_review_state_for_multiple_prs(), test_list_pull_requests_includes_not_run_review_state(), test_list_pull_requests_marks_different_head_sha_as_outdated() (+3 more)

### Community 42 - "Community 42"
Cohesion: 0.14
Nodes (13): app_models_github_app_installation, app_models_installation_repository, app_models_repository, app_models_user_repository_access, app_models_user_session, _post_login_redirect_url(), Request, _request_for_url() (+5 more)

### Community 43 - "Community 43"
Cohesion: 0.13
Nodes (15): _archive_url(), _default_runner_adapter(), _github_archive_headers(), _NoAuthOnRedirect, redacted_command(), _runner_resource_limits(), test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header() (+7 more)

### Community 44 - "Community 44"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 45 - "Community 45"
Cohesion: 0.13
Nodes (6): _get_cache(), _BrokenCache, _FakeCache, test_cache_operations_swallow_errors(), test_get_cache_returns_none_when_runtime_cache_ctor_fails(), test_get_cache_returns_none_when_vercel_import_fails()

### Community 46 - "Community 46"
Cohesion: 0.32
Nodes (13): AnalysisFinding, execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), Session, UUID (+5 more)

### Community 47 - "Community 47"
Cohesion: 0.23
Nodes (12): put, Session, UUID, update_quality_gate_config(), BaseModel, QualityGateConfigRead, QualityGateConfigUpdate, get_quality_gate_config() (+4 more)

### Community 48 - "Community 48"
Cohesion: 0.33
Nodes (12): _blocking_reasons(), build_final_report(), build_operational_error_report(), _list_section(), _pillar_section(), _snapshot_summary(), _string_list(), _suggestions() (+4 more)

### Community 49 - "Community 49"
Cohesion: 0.23
Nodes (13): getCoverageExecutionConfig(), updateCoverageExecutionConfig(), updateQualityGateConfig(), RepositoryQualityGateConfigPage, RepositoryWorkspaceContext, coveragePreset(), RepositoryQualityGateConfigPage(), enablePullRequestPublication() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.22
Nodes (11): app_core_config, app_core_errors, app_models_github_connection, app_models_oauth_state, app_models_user, app_services, build_login_url(), registered_oauth_callback_url() (+3 more)

### Community 51 - "Community 51"
Cohesion: 0.23
Nodes (8): decrypt_token(), encrypt_token(), _fernet(), generate_key(), test_token_crypto_round_trip(), test_token_crypto_requires_encryption_key(), test_exchange_code_for_user_success(), cryptography_fernet

### Community 52 - "Community 52"
Cohesion: 0.29
Nodes (9): logout(), App(), AuthenticatedApp(), handleLogout(), HelpPage, frontend_src_styles_app, react, react-dom (+1 more)

### Community 53 - "Community 53"
Cohesion: 0.27
Nodes (8): getRepository(), listAnalysisRuns(), RepositoryDetailPage, RunTicker(), RunTickerProps, tickClass(), RepositoryDetailPage(), AnalysisRunSummary

### Community 54 - "Community 54"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 55 - "Community 55"
Cohesion: 0.44
Nodes (9): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get, post, Session, UUID (+1 more)

### Community 56 - "Community 56"
Cohesion: 0.36
Nodes (9): GitHubPullRequestWithReviewState, get_repository_pull_request_context(), installation_client_for_repository(), list_repository_pull_requests(), Session, get_repository(), UUID, test_list_pull_requests_without_github_repo_id() (+1 more)

### Community 57 - "Community 57"
Cohesion: 0.29
Nodes (9): client(), db_session(), fixture, repository(), reset_database(), _reset_public_schema(), fastapi_testclient, pytest (+1 more)

### Community 58 - "Community 58"
Cohesion: 0.31
Nodes (6): _insert_run(), test_admin_execute_enqueues_run_and_returns_accepted(), test_get_analysis_run_detail(), test_list_analysis_runs_cache_miss_stores_repository_payload(), test_list_analysis_runs_for_repository(), test_non_admin_cannot_execute_or_publish_analysis()

### Community 59 - "Community 59"
Cohesion: 0.25
Nodes (9): post, Request, Session, receive_github_webhook(), GitHubWebhookResult, _has_valid_signature(), _ignored(), process_github_webhook() (+1 more)

### Community 60 - "Community 60"
Cohesion: 0.25
Nodes (7): _gate_result(), _insert_pending_run(), test_analysis_execution_reraises_app_error_and_missing_run(), test_analysis_execution_timeout_after_each_gate(), test_run_pipeline_time_budget_checks_between_gates(), load_run(), timeout_after()

### Community 62 - "Community 62"
Cohesion: 0.22
Nodes (8): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, routePrefix

### Community 63 - "Community 63"
Cohesion: 0.32
Nodes (7): get_install_url(), list_installations(), get, Session, GitHubInstallationRead, GitHubInstallUrlRead, BaseModel

### Community 64 - "Community 64"
Cohesion: 0.38
Nodes (7): _find_webhook_user(), _process_installation_event(), _pull_request_snapshot_from_payload(), Any, Session, test_webhook_find_user_without_sender(), test_webhook_installation_branches()

### Community 65 - "Community 65"
Cohesion: 0.38
Nodes (6): _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional(), json, skipif

### Community 66 - "Community 66"
Cohesion: 0.33
Nodes (3): github_writes(), fake_list(), fixture

### Community 73 - "Community 73"
Cohesion: 0.67
Nodes (3): _pull_request_context(), test_get_pull_request_context_maps_github_data_without_creating_run(), fake_context()

## Knowledge Gaps
- **80 isolated node(s):** `ErrorMessageProps`, `LoadingBlockProps`, `RunStatusDonutProps`, `AnalysisFinding`, `AnalysisTriggerSource` (+75 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 402 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 10` to `Community 1`, `Community 3`, `Community 4`, `Community 7`, `Community 8`, `Community 11`, `Community 13`, `Community 16`, `Community 20`, `Community 22`, `Community 23`, `Community 25`, `Community 29`, `Community 34`, `Community 36`, `Community 37`, `Community 40`, `Community 42`, `Community 43`, `Community 45`, `Community 46`, `Community 50`, `Community 51`, `Community 55`, `Community 56`, `Community 59`, `Community 63`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `AppError` connect `Community 10` to `Community 1`, `Community 3`, `Community 9`, `Community 13`, `Community 15`, `Community 16`, `Community 20`, `Community 21`, `Community 25`, `Community 27`, `Community 29`, `Community 31`, `Community 33`, `Community 37`, `Community 40`, `Community 46`, `Community 47`, `Community 50`, `Community 51`, `Community 55`, `Community 56`, `Community 59`, `Community 60`, `Community 63`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `AnalysisRun` connect `Community 25` to `Community 1`, `Community 4`, `Community 5`, `Community 7`, `Community 8`, `Community 15`, `Community 16`, `Community 21`, `Community 26`, `Community 27`, `Community 33`, `Community 34`, `Community 35`, `Community 36`, `Community 37`, `Community 39`, `Community 41`, `Community 46`, `Community 48`, `Community 58`, `Community 60`, `Community 61`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 67 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `AnalysisRun` (e.g. with `AnalysisRunStatus` and `AnalysisTriggerSource`) actually correct?**
  _`AnalysisRun` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `get_settings()` (e.g. with `build_login_url()` and `create_oauth_state()`) actually correct?**
  _`get_settings()` has 5 INFERRED edges - model-reasoned connections that need verification._