# Graph Report - Quality-Gate  (2026-11-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1796 nodes · 5501 edges · 88 communities (69 shown, 19 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 574 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `301f70da`
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

## Communities (88 total, 19 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (37): ChangedFileSnapshot, GitHubClient, _map_changed_file(), _map_pull_request(), _map_pull_request_snapshot(), test_github_client_raise_for_response_variants(), test_map_pull_request(), test_github_client_requires_token_and_maps_endpoints() (+29 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (44): GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult, analysis_run_target_url(), _client_for_run(), _get_run(), publication_frontend_origin(), publish_analysis_run_to_github() (+36 more)

### Community 2 - "Community 2"
Cohesion: 0.10
Nodes (26): _create_run(), _execute(), _gate_result(), github_writes(), fake_list(), _set_publish_flags(), _stub_passing_gates(), test_disabled_publication_flags_skip_github_writes() (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (19): AICoverageReview, AIGateFinding, AIReviewPartial, AISecurityReview, AITechDebtReview, BatchReviewOutput, ContextBudgetMetadata, InlineComment (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (28): parse_cobertura_xml(), parse_go_coverprofile(), parse_lcov(), flush(), calculate_total(), CoverageFile, CoverageReport, calculate_changed_files_coverage() (+20 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (34): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+26 more)

### Community 7 - "Community 7"
Cohesion: 0.16
Nodes (33): GitHubAppInstallation, GitHubConnection, InstallationRepository, UserRepositoryAccess, User, deactivate_installation(), get_active_installation_for_repository(), _get_paginated_github_resource() (+25 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (38): env, name, runs-on, services, steps, concurrency, cancel-in-progress, group (+30 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (34): API_BASE_URL, ApiError, getCookieValue(), getCoverageExecutionConfig(), getGitHubInstallUrl(), getHealth(), getPullRequestContext(), getQualityGateConfig() (+26 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (26): validate_runtime_security_settings(), tracing_enabled(), _parse_payload(), test_production_rejects_default_session_secret(), test_settings_ignore_blank_env_and_infer_vercel_production(), _fake_analysis_run(), test_allowed_file_paths_includes_string_changed_files(), test_collect_tool_results_dedupes_paths_and_falls_back_to_first_file() (+18 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (28): _blocking_severities(), build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner(), normalize_semgrep(), _normalize_severity() (+20 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (32): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+24 more)

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (36): getAnalysisRun(), publishAnalysisRunToGitHub(), EmptyState(), StatusBadge(), AIGateFindingItem(), AIReviewPanel(), AnalysisDetailPage(), handlePublish() (+28 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (36): environment, ALLOW_LOCAL_RUNNER_IN_PRODUCTION, API_HOST, API_PORT, APP_ENV, APP_NAME, AUTH_CALLBACK_URL, DATABASE_URL (+28 more)

### Community 15 - "Community 15"
Cohesion: 0.12
Nodes (24): executeAnalysisRun(), getCurrentUser(), getGitHubLoginUrl(), AnalysisDetailPage, App(), HelpPage, RepositoriesPage, RepositoryAnalysisRunsPage (+16 more)

### Community 16 - "Community 16"
Cohesion: 0.14
Nodes (21): claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), requeue_stale(), process_next_job(), run_forever() (+13 more)

### Community 17 - "Community 17"
Cohesion: 0.29
Nodes (5): Base, AnalysisJob, TimestampMixin, UUIDPrimaryKeyMixin, OAuthState

### Community 18 - "Community 18"
Cohesion: 0.11
Nodes (15): CoverageExecutionConfig, CoverageLanguage, CoverageExecutionConfigRead, CoverageExecutionConfigUpdate, build_coverage_execution_config(), get_coverage_execution_config(), map_github_language(), update_coverage_execution_config() (+7 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (16): build_login_url(), cleanup_expired_oauth_states(), consume_oauth_state(), create_oauth_state(), CreatedOAuthState, exchange_code_for_user(), _hash_oauth_value(), _oauth_state_is_valid() (+8 more)

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (16): database_health(), health(), readiness(), get_settings(), app_error_handler(), AppError, generate_app_jwt(), generate_installation_token() (+8 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (19): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), ChangedFileHunkArgs, collect_tool_results(), get_changed_file_hunk() (+11 more)

### Community 22 - "Community 22"
Cohesion: 0.09
Nodes (14): download_repository_archive(), _github_archive_headers(), repository_clone_url(), RepositoryRef, test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths(), _github_archive(), test_command_snapshot_redacts_clone_token() (+6 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (20): is_source_file(), analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), _python_complexity(), run_technical_debt_gate(), _suggestions() (+12 more)

### Community 24 - "Community 24"
Cohesion: 0.11
Nodes (12): Settings, Runner, create_runner_workspace(), RunnerWorkspace, test_runner_workspace_removes_existing_root(), test_settings_infer_vercel_skips_non_dict_and_existing_app_env(), test_production_defaults_to_isolated_runner_adapter(), test_production_rejects_local_runner_without_override() (+4 more)

### Community 25 - "Community 25"
Cohesion: 0.22
Nodes (24): AnalysisRunStatus, GateDecision, test_report_service_pass_summary_and_suggestions(), test_report_service_skipped_and_error_ai_review_paths(), _disable_github_publication(), _enable_github_publication(), _insert_run(), _open_pull_request() (+16 more)

### Community 26 - "Community 26"
Cohesion: 0.16
Nodes (23): UserSession, clear_session_cookies(), create_session(), CreatedSession, _decode_session(), get_user_for_session(), _hash_token(), revoke_session() (+15 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (16): get_dashboard_summary(), analyze_pull_request(), get_pull_request_context(), get_repository(), list_pull_requests(), list_repositories(), GitHubPullRequestWithReviewState, RepositoryRead (+8 more)

### Community 28 - "Community 28"
Cohesion: 0.26
Nodes (21): AnalysisRun, AnalysisTriggerSource, PullRequestContextRead, _build_pending_run(), _coerce_context(), _commit_new_run_or_reuse(), _create_or_reuse(), create_or_reuse_error_webhook_analysis_run() (+13 more)

### Community 29 - "Community 29"
Cohesion: 0.15
Nodes (18): _docker_run_command(), parse_repository_url(), run_isolated_command(), RunnerError, _validate_archive_members(), test_technical_debt_gate_missing_file_runner_error_and_suggestions(), prepare_head(), test_docker_run_command_rejects_invalid_network() (+10 more)

### Community 30 - "Community 30"
Cohesion: 0.11
Nodes (11): IsolatedRunnerWorkspace, _make_workspace_writable(), _remove_container(), run_command(), test_make_workspace_writable_skips_os_errors(), test_remove_container_swallows_errors(), test_runtime_cache_disabled_returns_none(), test_isolated_runner_workspace_paths() (+3 more)

### Community 31 - "Community 31"
Cohesion: 0.18
Nodes (19): DashboardBlockingCategory, DashboardFindingCount, DashboardOpenPullRequestAction, DashboardRecentAnalysisRun, DashboardSummaryRead, _action_for_open_pull_request(), _calculate_approval_rate(), _enum_value() (+11 more)

### Community 32 - "Community 32"
Cohesion: 0.26
Nodes (21): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+13 more)

### Community 33 - "Community 33"
Cohesion: 0.18
Nodes (15): build_graph(), compiled_review_graph(), _correct_draft(), draft(), emit(), load_evidence(), retrieve(), validate() (+7 more)

### Community 34 - "Community 34"
Cohesion: 0.17
Nodes (17): execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), _run_pipeline(), _skipped_gate(), run_coverage_gate() (+9 more)

### Community 35 - "Community 35"
Cohesion: 0.11
Nodes (14): CommandResult, test_evidence_workspace_prepare_base_and_path_guard(), run(), test_evidence_workspace_missing_base_sha_and_reprepare_revision(), run(), test_run_revision_coverage_missing_report_and_parse_formats(), run(), test_run_security_gate_python_scanners_in_run_path() (+6 more)

### Community 36 - "Community 36"
Cohesion: 0.14
Nodes (18): getDashboardSummary(), DashboardPage, AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts() (+10 more)

### Community 37 - "Community 37"
Cohesion: 0.09
Nodes (4): GateExecutionEvidenceWorkspace, test_base_coverage_skipped_when_no_drop_policy(), test_coverage_gate_runs_commands_in_configured_working_directory(), test_security_gate_uses_repository_token_for_clone()

### Community 38 - "Community 38"
Cohesion: 0.25
Nodes (3): get_current_user(), require_csrf_token(), get_db()

### Community 39 - "Community 39"
Cohesion: 0.19
Nodes (13): AnalysisFinding, CoverageReportFormat, FindingCategory, FindingSeverity, FindingSource, GateEvaluationMode, AnalysisFindingRead, QualityGateConfigRead (+5 more)

### Community 40 - "Community 40"
Cohesion: 0.10
Nodes (20): concurrency, cancel-in-progress, group, name, runs-on, steps, jobs, graph (+12 more)

### Community 41 - "Community 41"
Cohesion: 0.13
Nodes (5): get_me(), github_callback(), github_login(), logout(), CurrentUserRead

### Community 42 - "Community 42"
Cohesion: 0.22
Nodes (13): Repository, RepositoryCreate, create_repository(), get_repository_by_full_name(), list_repositories(), list_repositories_for_user(), test_create_repository_integrity_error(), test_repository_create_default_full_name() (+5 more)

### Community 43 - "Community 43"
Cohesion: 0.18
Nodes (10): _insert_analysis_run(), _patch_pull_requests(), fake_list_pull_requests(), _pull_request(), test_list_pull_requests_batches_review_state_for_multiple_prs(), test_list_pull_requests_includes_not_run_review_state(), test_list_pull_requests_marks_different_head_sha_as_outdated(), test_list_pull_requests_marks_matching_head_sha_as_current() (+2 more)

### Community 44 - "Community 44"
Cohesion: 0.14
Nodes (5): _post_login_redirect_url(), _request_for_url(), test_post_login_redirect_keeps_configured_frontend_origin_locally(), test_post_login_redirect_uses_callback_origin_on_vercel_host_mismatch(), test_post_login_redirect_uses_forwarded_https_origin_on_vercel_host_mismatch()

### Community 45 - "Community 45"
Cohesion: 0.22
Nodes (10): build_ai_review_input(), generate_ai_review_snapshot(), AIReviewSkipped, build_invocation_config(), configure_langsmith_from_settings(), _FakeRun, test_configure_langsmith_from_settings_copies_env(), test_generate_ai_review_snapshot_returns_error_when_graph_raises() (+2 more)

### Community 46 - "Community 46"
Cohesion: 0.16
Nodes (6): _archive_url(), _default_runner_adapter(), _NoAuthOnRedirect, _runner_resource_limits(), test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header()

### Community 47 - "Community 47"
Cohesion: 0.13
Nodes (8): expire_tags(), _get_cache(), _BrokenCache, _FakeCache, test_cache_operations_swallow_errors(), test_get_cache_returns_none_when_runtime_cache_ctor_fails(), test_get_cache_returns_none_when_vercel_import_fails(), test_get_json_returns_none_when_cache_disabled()

### Community 48 - "Community 48"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 49 - "Community 49"
Cohesion: 0.25
Nodes (8): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get_coverage_execution_config(), update_coverage_execution_config(), require_repository_admin(), AuthenticatedUser

### Community 50 - "Community 50"
Cohesion: 0.13
Nodes (15): command, depends_on, ports, volumes, postgres, condition, services, backend (+7 more)

### Community 51 - "Community 51"
Cohesion: 0.33
Nodes (10): GitHubPullRequestRead, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, get_pull_request_review_state(), get_pull_request_review_states(), _review_state_for_pull_request(), test_pull_request_review_state_helpers() (+2 more)

### Community 52 - "Community 52"
Cohesion: 0.19
Nodes (12): redact_text(), redacted_command(), _safe_env(), test_command_result_snapshot_redacts_output(), test_isolated_runner_does_not_pass_app_secrets_to_container(), test_redact_text_leaves_plain_text_untouched(), test_redact_text_masks_private_key_block(), test_redact_text_masks_tokens_and_clone_credentials() (+4 more)

### Community 53 - "Community 53"
Cohesion: 0.24
Nodes (6): get_quality_gate_config(), update_quality_gate_config(), QualityGateConfigUpdate, get_quality_gate_config(), update_quality_gate_config(), test_quality_gate_config_missing()

### Community 54 - "Community 54"
Cohesion: 0.14
Nodes (14): build, context, dockerfile, VITE_API_BASE_URL, build, depends_on, environment, ports (+6 more)

### Community 55 - "Community 55"
Cohesion: 0.19
Nodes (10): analyzePullRequest(), listPullRequests(), RepositoryPullRequestsPage, StatusBadgeProps, RepositoryWorkspaceContext, PullRequestTable(), RepositoryPullRequestsPage(), analyze() (+2 more)

### Community 56 - "Community 56"
Cohesion: 0.21
Nodes (8): decrypt_token(), encrypt_token(), _fernet(), generate_key(), test_token_crypto_round_trip(), test_token_crypto_requires_encryption_key(), test_exchange_code_for_user_success(), test_upsert_user_updates_existing_connection()

### Community 57 - "Community 57"
Cohesion: 0.15
Nodes (13): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, interval, retries, test, timeout, environment (+5 more)

### Community 58 - "Community 58"
Cohesion: 0.25
Nodes (6): _ai_review_response_schema(), _AIReviewJsonSchema, AnalysisRunDetail, AnalysisRunSummary, _inline_json_schema(), resolve()

### Community 59 - "Community 59"
Cohesion: 0.25
Nodes (7): AIReviewGenerated, _load_example(), test_graph_fail_coverage_passes_decision_lock_and_must_cite(), fake_draft(), test_graph_validation_failure_returns_ai_review_error(), fake_draft(), test_graph_draft_accepts_structured_and_dict_results()

### Community 60 - "Community 60"
Cohesion: 0.27
Nodes (8): getRepository(), listAnalysisRuns(), RepositoryDetailPage, RunTicker(), RunTickerProps, tickClass(), RepositoryDetailPage(), AnalysisRunSummary

### Community 61 - "Community 61"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 62 - "Community 62"
Cohesion: 0.31
Nodes (6): receive_github_webhook(), GitHubWebhookResult, _has_valid_signature(), _ignored(), process_github_webhook(), _pull_request_snapshot_from_payload()

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
Cohesion: 0.39
Nodes (4): get_install_url(), list_installations(), GitHubInstallationRead, GitHubInstallUrlRead

### Community 68 - "Community 68"
Cohesion: 0.33
Nodes (6): client(), db_session(), repository(), reset_database(), _reset_public_schema(), load_run()

### Community 70 - "Community 70"
Cohesion: 0.47
Nodes (4): _find_webhook_user(), _process_installation_event(), test_webhook_find_user_without_sender(), test_webhook_installation_branches()

### Community 71 - "Community 71"
Cohesion: 0.47
Nodes (4): _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional()

## Knowledge Gaps
- **5 isolated node(s):** `@types/node`, `@types/react`, `@types/react-dom`, `typescript`, `quality-gate-backend`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 486 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GitHubClient` connect `Community 0` to `Community 1`, `Community 2`, `Community 10`, `Community 43`, `Community 51`, `Community 20`, `Community 22`, `Community 27`, `Community 28`, `Community 30`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 67 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@types/node`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _5 weakly-connected nodes found - possible missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.06057692307692308 - nodes in this community are weakly interconnected._
- **Why does `AppError` connect `Community 20` to `Community 0`, `Community 1`, `Community 2`, `Community 7`, `Community 10`, `Community 18`, `Community 19`, `Community 25`, `Community 27`, `Community 28`, `Community 30`, `Community 34`, `Community 38`, `Community 42`, `Community 49`, `Community 53`, `Community 56`, `Community 62`, `Community 67`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.08417508417508418 - nodes in this community are weakly interconnected._