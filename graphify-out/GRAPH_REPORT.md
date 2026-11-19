# Graph Report - Quality-Gate  (2026-11-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1770 nodes · 5434 edges · 88 communities (68 shown, 20 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 574 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d819bf82`
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
- Community 77
- Community 87

## God Nodes (most connected - your core abstractions)
1. `AnalysisRunStatus` - 95 edges
2. `AppError` - 87 edges
3. `AnalysisRun` - 85 edges
4. `get_settings()` - 77 edges
5. `FindingCategory` - 64 edges
6. `GateDecision` - 56 edges
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
- 2-file cycle: `backend/app/db/base.py -> backend/app/models/analysis_finding.py -> backend/app/db/base.py`
- 2-file cycle: `backend/app/db/base.py -> backend/app/models/quality_gate_config.py -> backend/app/db/base.py`

## Communities (88 total, 20 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (37): ChangedFileSnapshot, GitHubClient, _map_changed_file(), _map_pull_request(), _map_pull_request_snapshot(), test_github_client_raise_for_response_variants(), test_map_pull_request(), test_github_client_requires_token_and_maps_endpoints() (+29 more)

### Community 1 - "Community 1"
Cohesion: 0.11
Nodes (31): parse_cobertura_xml(), parse_go_coverprofile(), parse_lcov(), flush(), calculate_total(), CoverageFile, CoverageReport, apply_coverage_policy() (+23 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (27): _create_run(), _execute(), _gate_result(), github_writes(), fake_list(), _set_publish_flags(), _stub_passing_gates(), test_disabled_publication_flags_skip_github_writes() (+19 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (30): validate_runtime_security_settings(), tracing_enabled(), _find_webhook_user(), _parse_payload(), _process_installation_event(), _pull_request_snapshot_from_payload(), test_production_rejects_default_session_secret(), test_settings_ignore_blank_env_and_infer_vercel_production() (+22 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (19): AICoverageReview, AIGateFinding, AIReviewPartial, AISecurityReview, AITechDebtReview, BatchReviewOutput, ContextBudgetMetadata, InlineComment (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (32): FindingCategory, FindingSeverity, AnalysisFindingRead, _blocking_severities(), build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit() (+24 more)

### Community 7 - "Community 7"
Cohesion: 0.16
Nodes (31): list_installations(), GitHubAppInstallation, GitHubConnection, InstallationRepository, UserRepositoryAccess, User, deactivate_installation(), get_active_installation_for_repository() (+23 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (38): env, name, runs-on, services, steps, concurrency, cancel-in-progress, group (+30 more)

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (19): build_graph(), compiled_review_graph(), _correct_draft(), draft(), emit(), load_evidence(), retrieve(), validate() (+11 more)

### Community 10 - "Community 10"
Cohesion: 0.23
Nodes (6): Base, AnalysisJob, TimestampMixin, UUIDPrimaryKeyMixin, OAuthState, UserSession

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (36): environment, ALLOW_LOCAL_RUNNER_IN_PRODUCTION, API_HOST, API_PORT, APP_ENV, APP_NAME, AUTH_CALLBACK_URL, DATABASE_URL (+28 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (31): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+23 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (16): cleanup_expired_oauth_states(), consume_oauth_state(), create_oauth_state(), CreatedOAuthState, exchange_code_for_user(), _hash_oauth_value(), _oauth_state_is_valid(), upsert_user_from_github() (+8 more)

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (19): get_coverage_execution_config(), update_coverage_execution_config(), get_dashboard_summary(), analyze_pull_request(), get_pull_request_context(), get_repository(), list_pull_requests(), list_repositories() (+11 more)

### Community 15 - "Community 15"
Cohesion: 0.10
Nodes (21): database_health(), health(), readiness(), AppError, generate_app_jwt(), generate_installation_token(), _private_key(), _get_paginated_github_resource() (+13 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (21): claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), requeue_stale(), process_next_job(), run_forever() (+13 more)

### Community 17 - "Community 17"
Cohesion: 0.10
Nodes (21): Settings, create_runner_workspace(), _default_runner_adapter(), _remove_container(), RunnerWorkspace, test_coverage_gate_is_source_file_variants(), test_remove_container_swallows_errors(), test_runner_workspace_removes_existing_root() (+13 more)

### Community 18 - "Community 18"
Cohesion: 0.11
Nodes (15): CoverageExecutionConfig, CoverageLanguage, CoverageExecutionConfigRead, CoverageExecutionConfigUpdate, build_coverage_execution_config(), get_coverage_execution_config(), map_github_language(), update_coverage_execution_config() (+7 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (21): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), ChangedFileHunkArgs, collect_tool_results(), get_changed_file_hunk() (+13 more)

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (24): API_BASE_URL, ApiError, getCookieValue(), getCurrentUser(), getGitHubInstallUrl(), getGitHubLoginUrl(), getHealth(), getPullRequestContext() (+16 more)

### Community 21 - "Community 21"
Cohesion: 0.20
Nodes (25): AnalysisRunStatus, GateDecision, _FakeRun, test_dashboard_action_fail_and_skip_none_action(), test_report_service_skipped_and_error_ai_review_paths(), _disable_github_publication(), _enable_github_publication(), _insert_run() (+17 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (19): _docker_run_command(), parse_repository_url(), redacted_command(), run_isolated_command(), _runner_resource_limits(), RunnerError, _validate_archive_members(), test_technical_debt_gate_missing_file_runner_error_and_suggestions() (+11 more)

### Community 23 - "Community 23"
Cohesion: 0.11
Nodes (26): getAnalysisRun(), getQualityGateConfig(), publishAnalysisRunToGitHub(), AnalysisDetailPage, AIReviewPanel(), AnalysisDetailPage(), handlePublish(), handleRetry() (+18 more)

### Community 24 - "Community 24"
Cohesion: 0.09
Nodes (22): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+14 more)

### Community 25 - "Community 25"
Cohesion: 0.17
Nodes (7): get_current_user(), require_csrf_token(), get_install_url(), app_error_handler(), get_db(), GitHubInstallationRead, GitHubInstallUrlRead

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (18): is_source_file(), analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), _python_complexity(), run_technical_debt_gate(), _suggestions() (+10 more)

### Community 27 - "Community 27"
Cohesion: 0.24
Nodes (21): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+13 more)

### Community 28 - "Community 28"
Cohesion: 0.11
Nodes (12): download_repository_archive(), repository_clone_url(), RepositoryRef, test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths(), _github_archive(), test_download_repository_archive_extracts_checkout_without_git(), test_parse_repository_url_extracts_installation_token() (+4 more)

### Community 29 - "Community 29"
Cohesion: 0.10
Nodes (14): Runner, CommandResult, test_evidence_workspace_prepare_base_and_path_guard(), run(), test_run_revision_coverage_missing_report_and_parse_formats(), run(), test_run_security_gate_python_scanners_in_run_path(), run() (+6 more)

### Community 30 - "Community 30"
Cohesion: 0.29
Nodes (20): AnalysisRun, AnalysisTriggerSource, PullRequestContextRead, _build_pending_run(), _coerce_context(), _commit_new_run_or_reuse(), _create_or_reuse(), create_or_reuse_error_webhook_analysis_run() (+12 more)

### Community 31 - "Community 31"
Cohesion: 0.17
Nodes (16): GitHubPullRequestRead, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, get_pull_request_review_state(), get_pull_request_review_states(), _review_state_for_pull_request(), _insert_pending_run() (+8 more)

### Community 32 - "Community 32"
Cohesion: 0.20
Nodes (17): DashboardBlockingCategory, DashboardFindingCount, DashboardOpenPullRequestAction, DashboardRecentAnalysisRun, DashboardSummaryRead, _action_for_open_pull_request(), _calculate_approval_rate(), _enum_value() (+9 more)

### Community 33 - "Community 33"
Cohesion: 0.14
Nodes (18): getDashboardSummary(), DashboardPage, AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts() (+10 more)

### Community 34 - "Community 34"
Cohesion: 0.09
Nodes (4): GateExecutionEvidenceWorkspace, test_base_coverage_skipped_when_no_drop_policy(), test_coverage_gate_runs_commands_in_configured_working_directory(), test_security_gate_uses_repository_token_for_clone()

### Community 35 - "Community 35"
Cohesion: 0.13
Nodes (17): analyzePullRequest(), executeAnalysisRun(), listPullRequests(), RepositoryAnalysisRunsPage, RepositoryPullRequestsPage, EmptyState(), EmptyStateProps, StatusBadge() (+9 more)

### Community 36 - "Community 36"
Cohesion: 0.21
Nodes (15): AnalysisFinding, execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), _run_pipeline(), _skipped_gate() (+7 more)

### Community 37 - "Community 37"
Cohesion: 0.26
Nodes (17): GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult, analysis_run_target_url(), _client_for_run(), _get_run(), publication_frontend_origin(), publish_analysis_run_to_github() (+9 more)

### Community 38 - "Community 38"
Cohesion: 0.10
Nodes (20): concurrency, cancel-in-progress, group, name, runs-on, steps, jobs, graph (+12 more)

### Community 39 - "Community 39"
Cohesion: 0.13
Nodes (5): get_me(), github_callback(), github_login(), logout(), CurrentUserRead

### Community 40 - "Community 40"
Cohesion: 0.19
Nodes (11): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), _ai_review_response_schema(), _AIReviewJsonSchema, AnalysisRunDetail, AnalysisRunSummary (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.18
Nodes (10): _insert_analysis_run(), _patch_pull_requests(), fake_list_pull_requests(), _pull_request(), test_list_pull_requests_batches_review_state_for_multiple_prs(), test_list_pull_requests_includes_not_run_review_state(), test_list_pull_requests_marks_different_head_sha_as_outdated(), test_list_pull_requests_marks_matching_head_sha_as_current() (+2 more)

### Community 42 - "Community 42"
Cohesion: 0.24
Nodes (12): Repository, RepositoryCreate, create_repository(), get_repository_by_full_name(), list_repositories(), list_repositories_for_user(), test_create_repository_integrity_error(), test_repository_create_default_full_name() (+4 more)

### Community 43 - "Community 43"
Cohesion: 0.16
Nodes (12): AIReviewGenerated, _load_example(), test_configure_langsmith_from_settings_copies_env(), test_error_snapshot_shape_unchanged(), test_generate_ai_review_snapshot_returns_error_when_graph_raises(), test_graph_fail_coverage_passes_decision_lock_and_must_cite(), fake_draft(), test_graph_validation_failure_returns_ai_review_error() (+4 more)

### Community 44 - "Community 44"
Cohesion: 0.15
Nodes (16): create_session(), CreatedSession, get_user_for_session(), _session_record_is_active(), set_session_cookies(), test_cookie_policy_helper_sets_secure_flags(), test_create_session_returns_raw_cookie_once(), test_csrf_token_validates_against_session_claim() (+8 more)

### Community 45 - "Community 45"
Cohesion: 0.19
Nodes (14): _create_run(), installation_token(), _raise_installation_token_error(), _set_publish_flags(), test_analysis_run_target_url_uses_frontend_origin_locally(), test_analysis_run_target_url_uses_vercel_production_host(), test_publish_commit_status_maps_decision(), test_publish_creates_marked_pull_request_comment() (+6 more)

### Community 46 - "Community 46"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 47 - "Community 47"
Cohesion: 0.15
Nodes (5): _post_login_redirect_url(), _request_for_url(), test_post_login_redirect_keeps_configured_frontend_origin_locally(), test_post_login_redirect_uses_callback_origin_on_vercel_host_mismatch(), test_post_login_redirect_uses_forwarded_https_origin_on_vercel_host_mismatch()

### Community 48 - "Community 48"
Cohesion: 0.17
Nodes (5): _archive_url(), _github_archive_headers(), _NoAuthOnRedirect, test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header()

### Community 49 - "Community 49"
Cohesion: 0.15
Nodes (7): IsolatedRunnerWorkspace, _make_workspace_writable(), run_command(), test_make_workspace_writable_skips_os_errors(), test_isolated_runner_workspace_paths(), test_run_command_success_and_writable_chmod_continue(), test_run_command_timeout()

### Community 50 - "Community 50"
Cohesion: 0.13
Nodes (15): command, depends_on, ports, volumes, postgres, condition, services, backend (+7 more)

### Community 51 - "Community 51"
Cohesion: 0.27
Nodes (6): get_quality_gate_config(), update_quality_gate_config(), QualityGateConfigUpdate, get_quality_gate_config(), update_quality_gate_config(), test_quality_gate_config_missing()

### Community 52 - "Community 52"
Cohesion: 0.30
Nodes (13): _blocking_reasons(), build_final_report(), build_operational_error_report(), _list_section(), _pillar_section(), _snapshot_summary(), _string_list(), _suggestions() (+5 more)

### Community 53 - "Community 53"
Cohesion: 0.29
Nodes (9): get_settings(), build_login_url(), registered_oauth_callback_url(), clear_session_cookies(), _decode_session(), _hash_token(), revoke_session(), validate_csrf_token() (+1 more)

### Community 54 - "Community 54"
Cohesion: 0.14
Nodes (14): build, context, dockerfile, VITE_API_BASE_URL, build, depends_on, environment, ports (+6 more)

### Community 55 - "Community 55"
Cohesion: 0.23
Nodes (13): getCoverageExecutionConfig(), updateCoverageExecutionConfig(), updateQualityGateConfig(), RepositoryQualityGateConfigPage, RepositoryWorkspaceContext, coveragePreset(), RepositoryQualityGateConfigPage(), enablePullRequestPublication() (+5 more)

### Community 56 - "Community 56"
Cohesion: 0.24
Nodes (11): redact_text(), _safe_env(), test_redact_json_like_redacts_nested_patch_without_mutating_input(), test_redact_text_masks_github_tokens_private_keys_and_assignments(), test_command_result_snapshot_redacts_output(), test_redact_text_leaves_plain_text_untouched(), test_redact_text_masks_private_key_block(), test_redact_text_masks_tokens_and_clone_credentials() (+3 more)

### Community 57 - "Community 57"
Cohesion: 0.15
Nodes (13): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, interval, retries, test, timeout, environment (+5 more)

### Community 58 - "Community 58"
Cohesion: 0.29
Nodes (8): logout(), App(), AuthenticatedApp(), handleLogout(), HelpPage, react, react-dom, react-router-dom

### Community 59 - "Community 59"
Cohesion: 0.31
Nodes (7): GitHubPullRequestWithReviewState, get_repository_pull_request_context(), installation_client_for_repository(), list_repository_pull_requests(), get_repository(), test_list_pull_requests_without_github_repo_id(), test_get_repository_not_found()

### Community 60 - "Community 60"
Cohesion: 0.27
Nodes (8): getRepository(), listAnalysisRuns(), RepositoryDetailPage, RunTicker(), RunTickerProps, tickClass(), RepositoryDetailPage(), AnalysisRunSummary

### Community 61 - "Community 61"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 62 - "Community 62"
Cohesion: 0.31
Nodes (4): CoverageReportFormat, FindingSource, GateEvaluationMode, QualityGateConfigRead

### Community 63 - "Community 63"
Cohesion: 0.22
Nodes (3): QualityGateConfig, test_manual_analyze_enqueues_pending_run(), test_manual_analyze_uses_coverage_working_directory_for_nested_project()

### Community 65 - "Community 65"
Cohesion: 0.31
Nodes (6): _insert_run(), test_admin_execute_enqueues_run_and_returns_accepted(), test_get_analysis_run_detail(), test_list_analysis_runs_cache_miss_stores_repository_payload(), test_list_analysis_runs_for_repository(), test_non_admin_cannot_execute_or_publish_analysis()

### Community 66 - "Community 66"
Cohesion: 0.20
Nodes (9): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, framework (+1 more)

### Community 67 - "Community 67"
Cohesion: 0.29
Nodes (5): receive_github_webhook(), GitHubWebhookResult, _has_valid_signature(), _ignored(), process_github_webhook()

### Community 68 - "Community 68"
Cohesion: 0.36
Nodes (5): client(), db_session(), reset_database(), _reset_public_schema(), load_run()

### Community 70 - "Community 70"
Cohesion: 0.38
Nodes (4): _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional()

## Knowledge Gaps
- **5 isolated node(s):** `@types/node`, `@types/react`, `@types/react-dom`, `typescript`, `quality-gate-backend`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 481 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 53` to `Community 0`, `Community 3`, `Community 7`, `Community 9`, `Community 10`, `Community 13`, `Community 14`, `Community 15`, `Community 16`, `Community 17`, `Community 22`, `Community 25`, `Community 28`, `Community 36`, `Community 37`, `Community 40`, `Community 44`, `Community 48`, `Community 49`, `Community 51`, `Community 59`, `Community 67`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 67 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@types/node`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _5 weakly-connected nodes found - possible missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.06349206349206349 - nodes in this community are weakly interconnected._
- **Why does `AppError` connect `Community 15` to `Community 0`, `Community 2`, `Community 3`, `Community 7`, `Community 13`, `Community 14`, `Community 17`, `Community 18`, `Community 21`, `Community 25`, `Community 30`, `Community 31`, `Community 36`, `Community 37`, `Community 40`, `Community 42`, `Community 45`, `Community 51`, `Community 53`, `Community 59`, `Community 67`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.11304347826086956 - nodes in this community are weakly interconnected._