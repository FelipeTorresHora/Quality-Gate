# Graph Report - workspace  (2026-09-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1549 nodes · 5121 edges · 72 communities (59 shown, 13 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 540 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7a021771`
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
- Community 65
- Community 71

## God Nodes (most connected - your core abstractions)
1. `AnalysisRunStatus` - 95 edges
2. `AppError` - 94 edges
3. `AnalysisRun` - 85 edges
4. `get_settings()` - 78 edges
5. `User` - 61 edges
6. `GateDecision` - 56 edges
7. `FindingCategory` - 55 edges
8. `GitHubClient` - 51 edges
9. `Repository` - 51 edges
10. `AnalysisTriggerSource` - 50 edges

## Surprising Connections (you probably didn't know these)
- `list_installations()` --uses--> `AuthenticatedUser`  [INFERRED]
  backend/app/api/routes_github_installations.py → backend/app/services/session_service.py
- `GitHubClient` --uses--> `PullRequestContextRead`  [INFERRED]
  backend/app/services/github_service.py → backend/app/schemas/github.py
- `analyze_pull_request()` --uses--> `AnalysisRunStatus`  [INFERRED]
  backend/app/api/routes_repositories.py → backend/app/models/enums.py
- `AnalysisRun` --uses--> `AnalysisRunStatus`  [INFERRED]
  backend/app/models/analysis_run.py → backend/app/models/enums.py
- `AnalysisRunSummary` --uses--> `AnalysisRunStatus`  [INFERRED]
  backend/app/schemas/analysis.py → backend/app/models/enums.py

## Import Cycles
- None detected.

## Communities (72 total, 13 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (79): get_current_user(), Request, Session, require_csrf_token(), execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github() (+71 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (61): post, Request, Session, receive_github_webhook(), GitHubWebhookResult, PullRequestContextRead, _build_pending_run(), _coerce_context() (+53 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (40): ChangedFileSnapshot, GitHubPullRequestRead, GitHubPullRequestWithReviewState, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, BaseModel, get_repository_pull_request_context() (+32 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (43): app_error_handler(), AppError, Exception, Request, OAuthState, generate_app_jwt(), generate_installation_token(), _private_key() (+35 more)

### Community 4 - "Community 4"
Cohesion: 0.10
Nodes (46): github_callback(), github_login(), logout(), _post_login_redirect_url(), get, post, Request, Response (+38 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (3): alembic, collections_abc, sqlalchemy_dialects

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (31): GitHubAppInstallation, GitHubConnection, InstallationRepository, UserRepositoryAccess, deactivate_installation(), get_active_installation_for_repository(), _get_paginated_github_resource(), _get_paginated_user_resource() (+23 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (19): CoverageExecutionConfig, CoverageLanguage, CoverageExecutionConfigUpdate, BaseModel, model_validator, build_coverage_execution_config(), get_coverage_execution_config(), map_github_language() (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (31): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+23 more)

### Community 9 - "Community 9"
Cohesion: 0.27
Nodes (12): Base, TimestampMixin, UUIDPrimaryKeyMixin, QualityGateConfig, datetime, DeclarativeBase, logging_config, sqlalchemy (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (25): AnalysisJob, claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), timedelta, UUID (+17 more)

### Community 11 - "Community 11"
Cohesion: 0.19
Nodes (26): AnalysisRunStatus, GateDecision, _FakeRun, test_dashboard_action_fail_and_skip_none_action(), test_report_service_pass_summary_and_suggestions(), test_report_service_skipped_and_error_ai_review_paths(), _disable_github_publication(), _enable_github_publication() (+18 more)

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (24): API_BASE_URL, ApiError, getCookieValue(), getCurrentUser(), getGitHubInstallUrl(), getGitHubLoginUrl(), getHealth(), getPullRequestContext() (+16 more)

### Community 13 - "Community 13"
Cohesion: 0.10
Nodes (23): Any, model_validator, Settings, validate_runtime_security_settings(), create_runner_workspace(), _default_runner_adapter(), UUID, RunnerWorkspace (+15 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (19): invoke_review_tools(), Invoke the four tools so LangSmith can record tool spans when tracing is on., tracing_enabled(), test_invoke_review_tools_fallback_changed_file_without_blocking_hunks(), _fake_analysis_run(), test_build_final_report_delegates_to_operational_error(), test_collect_tool_results_dedupes_paths_and_falls_back_to_first_file(), test_coverage_gate_requires_base_and_head_sha() (+11 more)

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (27): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), ChangedFileHunkArgs, collect_tool_results(), get_changed_file_hunk() (+19 more)

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (26): getAnalysisRun(), getQualityGateConfig(), publishAnalysisRunToGitHub(), AnalysisDetailPage, AIReviewPanel(), AnalysisDetailPage(), handlePublish(), handleRetry() (+18 more)

### Community 17 - "Community 17"
Cohesion: 0.09
Nodes (22): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+14 more)

### Community 18 - "Community 18"
Cohesion: 0.21
Nodes (25): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+17 more)

### Community 19 - "Community 19"
Cohesion: 0.15
Nodes (21): _docker_run_command(), parse_repository_url(), Exception, Path, run_isolated_command(), RunnerError, _validate_archive_members(), test_technical_debt_gate_missing_file_runner_error_and_suggestions() (+13 more)

### Community 20 - "Community 20"
Cohesion: 0.21
Nodes (22): _create_run(), _execute(), _gate_result(), _set_publish_flags(), _stub_passing_gates(), test_disabled_publication_flags_skip_github_writes(), test_execute_aborts_when_total_time_budget_exceeded(), test_execute_marks_error_on_unexpected_exception() (+14 more)

### Community 21 - "Community 21"
Cohesion: 0.10
Nodes (16): _blocking_severities(), parse_json_output(), run_security_gate(), _scanner_commands(), test_blocking_severities_from_dict_and_list(), test_normalize_scanner_unknown_returns_empty(), test_parse_json_output_invalid_json(), test_run_security_gate_empty_scanner_output() (+8 more)

### Community 22 - "Community 22"
Cohesion: 0.10
Nodes (14): Runner, CommandResult, test_evidence_workspace_missing_base_sha_and_reprepare_revision(), run(), test_run_revision_coverage_missing_report_and_parse_formats(), run(), test_run_security_gate_python_scanners_in_run_path(), run() (+6 more)

### Community 23 - "Community 23"
Cohesion: 0.20
Nodes (22): DashboardBlockingCategory, DashboardFindingCount, DashboardOpenPullRequestAction, DashboardRecentAnalysisRun, DashboardSummaryRead, BaseModel, _action_for_open_pull_request(), _calculate_approval_rate() (+14 more)

### Community 24 - "Community 24"
Cohesion: 0.19
Nodes (20): build_graph(), _correct_draft(), draft(), emit(), load_evidence(), Any, retrieve(), validate() (+12 more)

### Community 25 - "Community 25"
Cohesion: 0.14
Nodes (18): getDashboardSummary(), DashboardPage, AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts() (+10 more)

### Community 26 - "Community 26"
Cohesion: 0.19
Nodes (15): AnalysisRun, AnalysisTriggerSource, CoverageReportFormat, build_ai_review_input(), test_build_ai_review_input_redacts_diff_changed_files_and_findings(), _insert_pending_run(), test_commit_new_run_or_reuse_integrity_error_path(), test_commit_new_run_or_reuse_reraises_when_duplicate_missing() (+7 more)

### Community 27 - "Community 27"
Cohesion: 0.09
Nodes (14): parse_cobertura_xml(), Path, _remove_container(), test_cobertura_parser_skips_missing_filename_and_merges_classes(), test_evidence_workspace_prepare_base_and_path_guard(), run(), test_make_workspace_writable_skips_os_errors(), test_remove_container_swallows_errors() (+6 more)

### Community 28 - "Community 28"
Cohesion: 0.13
Nodes (17): analyzePullRequest(), executeAnalysisRun(), listPullRequests(), RepositoryAnalysisRunsPage, RepositoryPullRequestsPage, EmptyState(), EmptyStateProps, StatusBadge() (+9 more)

### Community 29 - "Community 29"
Cohesion: 0.19
Nodes (19): AST, analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), Path, _python_complexity(), run_technical_debt_gate() (+11 more)

### Community 30 - "Community 30"
Cohesion: 0.30
Nodes (19): FindingCategory, FindingSeverity, AnalysisFindingRead, build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner() (+11 more)

### Community 31 - "Community 31"
Cohesion: 0.24
Nodes (20): AnalysisRunDetail, AnalysisRunSummary, GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult, BaseModel, _client_for_run(), _get_run() (+12 more)

### Community 32 - "Community 32"
Cohesion: 0.18
Nodes (17): analysis_run_target_url(), publication_frontend_origin(), _create_run(), installation_token(), fixture, _raise_installation_token_error(), _set_publish_flags(), test_analysis_run_target_url_uses_frontend_origin_locally() (+9 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (17): _archive_url(), _NoAuthOnRedirect, redacted_command(), _runner_resource_limits(), test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header(), test_redacted_command_masks_token(), email_message (+9 more)

### Community 34 - "Community 34"
Cohesion: 0.12
Nodes (8): download_repository_archive(), _github_archive_headers(), RepositoryRef, test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths(), test_parse_repository_url_extracts_installation_token(), test_download_repository_archive_http_error(), test_download_repository_archive_success()

### Community 35 - "Community 35"
Cohesion: 0.18
Nodes (11): _insert_analysis_run(), _patch_pull_requests(), fake_list_pull_requests(), _pull_request(), datetime, test_list_pull_requests_batches_review_state_for_multiple_prs(), test_list_pull_requests_includes_not_run_review_state(), test_list_pull_requests_marks_different_head_sha_as_outdated() (+3 more)

### Community 36 - "Community 36"
Cohesion: 0.24
Nodes (15): Repository, BaseModel, model_validator, RepositoryCreate, create_repository(), get_repository_by_full_name(), list_repositories(), list_repositories_for_user() (+7 more)

### Community 37 - "Community 37"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 38 - "Community 38"
Cohesion: 0.24
Nodes (15): AnalysisFinding, execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), Session, UUID (+7 more)

### Community 39 - "Community 39"
Cohesion: 0.18
Nodes (3): GateExecutionEvidenceWorkspace, PreparedRevision, Path

### Community 40 - "Community 40"
Cohesion: 0.20
Nodes (12): parse_lcov(), flush(), Path, calculate_total(), CoverageFile, test_coverage_file_percentage_when_total_zero(), test_parse_lcov_coverage(), test_coverage_file_and_calculate_total_edge_cases() (+4 more)

### Community 41 - "Community 41"
Cohesion: 0.15
Nodes (12): repository_clone_url(), _github_archive(), _github_response(), test_command_snapshot_redacts_clone_token(), test_download_repository_archive_extracts_checkout_without_git(), test_github_client_uses_provided_installation_token(), fake_get(), test_pull_request_context_maps_paginated_files_and_truncates_large_diff() (+4 more)

### Community 42 - "Community 42"
Cohesion: 0.25
Nodes (16): CoverageReport, calculate_changed_files_coverage(), is_source_file(), _lookup_coverage(), _match_keys(), _normalize_path(), Any, test_coverage_gate_is_source_file_variants() (+8 more)

### Community 43 - "Community 43"
Cohesion: 0.33
Nodes (12): _blocking_reasons(), build_final_report(), build_operational_error_report(), _list_section(), _pillar_section(), _snapshot_summary(), _string_list(), _suggestions() (+4 more)

### Community 44 - "Community 44"
Cohesion: 0.16
Nodes (6): IsolatedRunnerWorkspace, _make_workspace_writable(), run_command(), test_isolated_runner_workspace_paths(), test_run_command_success_and_writable_chmod_continue(), test_run_command_timeout()

### Community 45 - "Community 45"
Cohesion: 0.23
Nodes (13): getCoverageExecutionConfig(), updateCoverageExecutionConfig(), updateQualityGateConfig(), RepositoryQualityGateConfigPage, RepositoryWorkspaceContext, coveragePreset(), RepositoryQualityGateConfigPage(), enablePullRequestPublication() (+5 more)

### Community 46 - "Community 46"
Cohesion: 0.26
Nodes (10): compiled_review_graph(), generate_ai_review_snapshot(), AIReviewError, AIReviewSkipped, BaseModel, build_invocation_config(), Any, test_generate_ai_review_snapshot_returns_error_when_graph_raises() (+2 more)

### Community 47 - "Community 47"
Cohesion: 0.22
Nodes (11): parse_go_coverprofile(), Path, apply_coverage_policy(), ChangedCoverageResult, _parse_report(), Path, run_coverage_gate(), _run_revision_coverage() (+3 more)

### Community 48 - "Community 48"
Cohesion: 0.24
Nodes (10): Any, redact_json_like(), redact_text(), text_contains_secrets(), test_redact_json_like_redacts_nested_patch_without_mutating_input(), test_redact_text_masks_github_tokens_private_keys_and_assignments(), test_redact_text_leaves_plain_text_untouched(), test_redact_text_masks_private_key_block() (+2 more)

### Community 49 - "Community 49"
Cohesion: 0.29
Nodes (9): logout(), App(), AuthenticatedApp(), handleLogout(), HelpPage, frontend_src_styles_app, react, react-dom (+1 more)

### Community 50 - "Community 50"
Cohesion: 0.24
Nodes (9): load_examples(), main(), Push the git-versioned AI review golden dataset to LangSmith as qg-ai-…, _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional(), json (+1 more)

### Community 51 - "Community 51"
Cohesion: 0.27
Nodes (8): getRepository(), listAnalysisRuns(), RepositoryDetailPage, RunTicker(), RunTickerProps, tickClass(), RepositoryDetailPage(), AnalysisRunSummary

### Community 52 - "Community 52"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.31
Nodes (9): client(), create_user_repo_access(), create(), db_session(), fixture, reset_database(), _reset_public_schema(), fastapi_testclient (+1 more)

### Community 54 - "Community 54"
Cohesion: 0.31
Nodes (6): _insert_run(), test_admin_execute_enqueues_run_and_returns_accepted(), test_get_analysis_run_detail(), test_list_analysis_runs_cache_miss_stores_repository_payload(), test_list_analysis_runs_for_repository(), test_non_admin_cannot_execute_or_publish_analysis()

### Community 55 - "Community 55"
Cohesion: 0.39
Nodes (7): get_install_url(), list_installations(), get, Session, GitHubInstallationRead, GitHubInstallUrlRead, BaseModel

### Community 56 - "Community 56"
Cohesion: 0.22
Nodes (8): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, routePrefix

### Community 57 - "Community 57"
Cohesion: 0.36
Nodes (6): _safe_env(), test_command_result_snapshot_redacts_output(), test_isolated_runner_does_not_pass_app_secrets_to_container(), test_safe_env_defaults_path_when_absent(), test_safe_env_does_not_leak_app_secrets(), test_safe_env_keeps_toolchain_variables()

### Community 58 - "Community 58"
Cohesion: 0.33
Nodes (3): github_writes(), fake_list(), fixture

## Knowledge Gaps
- **80 isolated node(s):** `ErrorMessageProps`, `LoadingBlockProps`, `RunStatusDonutProps`, `AnalysisFinding`, `AnalysisTriggerSource` (+75 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 383 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 6`, `Community 9`, `Community 13`, `Community 14`, `Community 19`, `Community 24`, `Community 27`, `Community 31`, `Community 32`, `Community 33`, `Community 34`, `Community 38`, `Community 44`, `Community 46`, `Community 55`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `AppError` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 32`, `Community 36`, `Community 4`, `Community 38`, `Community 7`, `Community 6`, `Community 11`, `Community 14`, `Community 20`, `Community 55`, `Community 26`, `Community 27`, `Community 31`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 13` to `Community 0`, `Community 2`, `Community 4`, `Community 44`, `Community 46`, `Community 14`, `Community 15`, `Community 19`, `Community 22`, `Community 57`, `Community 27`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 67 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `AnalysisRun` (e.g. with `AnalysisRunStatus` and `AnalysisTriggerSource`) actually correct?**
  _`AnalysisRun` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `User` (e.g. with `get_dashboard_summary()` and `_remove_stale_user_installation_access()`) actually correct?**
  _`User` has 15 INFERRED edges - model-reasoned connections that need verification._