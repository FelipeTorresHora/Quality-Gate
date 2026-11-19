# Graph Report - Quality-Gate  (2026-11-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1846 nodes · 5662 edges · 96 communities (69 shown, 27 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 577 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5227fb7b`
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
- Community 75
- Community 76
- Community 77
- Community 79
- Community 80
- Community 81
- Community 85
- Community 95

## God Nodes (most connected - your core abstractions)
1. `AnalysisRunStatus` - 95 edges
2. `AppError` - 90 edges
3. `AnalysisRun` - 85 edges
4. `get_settings()` - 80 edges
5. `FindingCategory` - 62 edges
6. `GateDecision` - 56 edges
7. `GitHubClient` - 51 edges
8. `AnalysisTriggerSource` - 50 edges
9. `Repository` - 50 edges
10. `User` - 45 edges

## Surprising Connections (you probably didn't know these)
- `test_manual_analyze_enqueues_pending_run()` --uses--> `AnalysisTriggerSource`  [INFERRED]
  backend/tests/test_manual_pr_analysis.py → backend/app/models/enums.py
- `GateExecutionEvidenceWorkspace` --uses--> `AnalysisRun`  [INFERRED]
  backend/app/services/analysis_evidence_workspace.py → backend/app/models/analysis_run.py
- `GateExecutionEvidenceWorkspace` --uses--> `Repository`  [INFERRED]
  backend/app/services/analysis_evidence_workspace.py → backend/app/models/repository.py
- `GateExecutionEvidenceWorkspace` --uses--> `RunnerError`  [INFERRED]
  backend/app/services/analysis_evidence_workspace.py → backend/app/services/runner_service.py
- `run_security_gate()` --uses--> `GateExecutionEvidenceWorkspace`  [INFERRED]
  backend/app/services/gates/security_gate.py → backend/app/services/analysis_evidence_workspace.py

## Import Cycles
- 2-file cycle: `backend/app/db/base.py -> backend/app/models/analysis_finding.py -> backend/app/db/base.py`
- 2-file cycle: `backend/app/db/base.py -> backend/app/models/quality_gate_config.py -> backend/app/db/base.py`

## Communities (96 total, 27 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (44): GateExecutionEvidenceWorkspace, PreparedRevision, parse_cobertura_xml(), parse_go_coverprofile(), _span_lines(), parse_lcov(), flush(), calculate_total() (+36 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (43): ChangedFileSnapshot, GitHubPullRequestRead, GitHubPullRequestWithReviewState, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, get_repository_pull_request_context(), GitHubClient (+35 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (51): _alert_paths(), _as_text(), _block(), _bound_sections(), build_coverage_digest(), build_debt_digest(), build_security_digest(), selected() (+43 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (22): app_error_handler(), AppError, _action_for_open_pull_request(), _snapshot_html_url(), generate_app_jwt(), generate_installation_token(), _private_key(), boom() (+14 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (19): AICoverageReview, AIGateFinding, AIReviewPartial, AISecurityReview, AITechDebtReview, BatchReviewOutput, ContextBudgetMetadata, InlineComment (+11 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (38): env, name, runs-on, services, steps, concurrency, cancel-in-progress, group (+30 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (24): Settings, validate_runtime_security_settings(), create_runner_workspace(), _default_runner_adapter(), IsolatedRunnerWorkspace, RunnerWorkspace, test_production_rejects_default_session_secret(), test_runner_workspace_removes_existing_root() (+16 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (36): environment, ALLOW_LOCAL_RUNNER_IN_PRODUCTION, API_HOST, API_PORT, APP_ENV, APP_NAME, AUTH_CALLBACK_URL, DATABASE_URL (+28 more)

### Community 9 - "Community 9"
Cohesion: 0.06
Nodes (31): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+23 more)

### Community 10 - "Community 10"
Cohesion: 0.21
Nodes (28): GitHubAppInstallation, GitHubConnection, InstallationRepository, UserRepositoryAccess, User, deactivate_installation(), get_active_installation_for_repository(), _permission_name() (+20 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (22): AnalysisJob, claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), requeue_stale(), process_next_job() (+14 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (16): get_dashboard_summary(), analyze_pull_request(), get_pull_request_context(), get_repository(), list_pull_requests(), list_repositories(), RepositoryRead, expire_tags() (+8 more)

### Community 13 - "Community 13"
Cohesion: 0.29
Nodes (5): Base, TimestampMixin, UUIDPrimaryKeyMixin, OAuthState, UserSession

### Community 14 - "Community 14"
Cohesion: 0.18
Nodes (27): AnalysisRunStatus, GateDecision, _FakeRun, test_report_service_pass_summary_and_suggestions(), test_report_service_skipped_and_error_ai_review_paths(), _disable_github_publication(), _enable_github_publication(), _insert_run() (+19 more)

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (25): _ai_review_response_schema(), _AIReviewJsonSchema, AnalysisFindingRead, AnalysisRunDetail, AnalysisRunSummary, GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult (+17 more)

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (15): CoverageExecutionConfig, CoverageLanguage, CoverageExecutionConfigRead, CoverageExecutionConfigUpdate, build_coverage_execution_config(), get_coverage_execution_config(), map_github_language(), update_coverage_execution_config() (+7 more)

### Community 17 - "Community 17"
Cohesion: 0.13
Nodes (24): API_BASE_URL, ApiError, getCookieValue(), getCurrentUser(), getGitHubInstallUrl(), getGitHubLoginUrl(), getHealth(), getPullRequestContext() (+16 more)

### Community 18 - "Community 18"
Cohesion: 0.09
Nodes (15): Runner, CommandResult, test_evidence_workspace_prepare_base_and_path_guard(), run(), test_evidence_workspace_missing_base_sha_and_reprepare_revision(), run(), test_run_revision_coverage_missing_report_and_parse_formats(), run() (+7 more)

### Community 19 - "Community 19"
Cohesion: 0.11
Nodes (26): getAnalysisRun(), getQualityGateConfig(), publishAnalysisRunToGitHub(), AnalysisDetailPage, AIReviewPanel(), AnalysisDetailPage(), handlePublish(), handleRetry() (+18 more)

### Community 20 - "Community 20"
Cohesion: 0.09
Nodes (22): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+14 more)

### Community 21 - "Community 21"
Cohesion: 0.16
Nodes (23): get_settings(), clear_session_cookies(), create_session(), CreatedSession, _decode_session(), get_user_for_session(), _hash_token(), revoke_session() (+15 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (14): download_repository_archive(), _github_archive_headers(), parse_repository_url(), redacted_command(), RepositoryRef, test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths(), test_parse_repository_url_extracts_installation_token() (+6 more)

### Community 23 - "Community 23"
Cohesion: 0.09
Nodes (16): invoke_review_tools(), tracing_enabled(), test_invoke_review_tools_fallback_changed_file_without_blocking_hunks(), _fake_analysis_run(), test_allowed_file_paths_includes_string_changed_files(), test_compiled_review_graph_is_cached(), test_coverage_gate_is_source_file_branches(), test_decision_lock_requires_blocking_reasons_on_fail() (+8 more)

### Community 24 - "Community 24"
Cohesion: 0.21
Nodes (22): _create_run(), _execute(), _gate_result(), _set_publish_flags(), _stub_passing_gates(), test_disabled_publication_flags_skip_github_writes(), test_execute_aborts_when_total_time_budget_exceeded(), test_execute_marks_error_on_unexpected_exception() (+14 more)

### Community 25 - "Community 25"
Cohesion: 0.27
Nodes (21): AnalysisRun, AnalysisTriggerSource, PullRequestContextRead, _build_pending_run(), _coerce_context(), _commit_new_run_or_reuse(), _create_or_reuse(), create_or_reuse_error_webhook_analysis_run() (+13 more)

### Community 26 - "Community 26"
Cohesion: 0.15
Nodes (18): analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), _python_complexity(), run_technical_debt_gate(), _suggestions(), validate_diff_evidence() (+10 more)

### Community 27 - "Community 27"
Cohesion: 0.12
Nodes (19): GitHubWebhookResult, _get_paginated_github_resource(), _get_paginated_user_resource(), list_installation_repositories(), _find_webhook_user(), _has_valid_signature(), _ignored(), _parse_payload() (+11 more)

### Community 28 - "Community 28"
Cohesion: 0.16
Nodes (19): _patch_context(), fake_context(), _post_webhook(), _pull_request_context(), _pull_request_payload(), _signed_headers(), test_pull_request_webhook_creates_pending_analysis_run(), test_pull_request_webhook_is_idempotent_for_same_repository_pr_and_head_sha() (+11 more)

### Community 29 - "Community 29"
Cohesion: 0.26
Nodes (21): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+13 more)

### Community 30 - "Community 30"
Cohesion: 0.14
Nodes (18): getDashboardSummary(), DashboardPage, AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts() (+10 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (16): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), collect_tool_results(), get_changed_file_hunk(), get_gate_summary() (+8 more)

### Community 32 - "Community 32"
Cohesion: 0.13
Nodes (17): analyzePullRequest(), executeAnalysisRun(), listPullRequests(), RepositoryAnalysisRunsPage, RepositoryPullRequestsPage, EmptyState(), EmptyStateProps, StatusBadge() (+9 more)

### Community 33 - "Community 33"
Cohesion: 0.21
Nodes (14): Repository, RepositoryCreate, create_repository(), get_repository(), get_repository_by_full_name(), list_repositories(), list_repositories_for_user(), test_create_repository_integrity_error() (+6 more)

### Community 34 - "Community 34"
Cohesion: 0.13
Nodes (12): _docker_run_command(), run_isolated_command(), _runner_resource_limits(), RunnerError, _validate_archive_members(), test_technical_debt_gate_missing_file_runner_error_and_suggestions(), prepare_head(), test_docker_run_command_rejects_invalid_network() (+4 more)

### Community 35 - "Community 35"
Cohesion: 0.27
Nodes (3): get_current_user(), require_csrf_token(), get_db()

### Community 36 - "Community 36"
Cohesion: 0.10
Nodes (20): concurrency, cancel-in-progress, group, name, runs-on, steps, jobs, graph (+12 more)

### Community 37 - "Community 37"
Cohesion: 0.25
Nodes (9): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get_coverage_execution_config(), update_coverage_execution_config(), require_repository_access(), require_repository_admin() (+1 more)

### Community 38 - "Community 38"
Cohesion: 0.20
Nodes (11): AnalysisFinding, CoverageReportFormat, FindingSeverity, FindingSource, test_build_ai_review_input_redacts_diff_changed_files_and_findings(), _insert_run(), test_admin_execute_enqueues_run_and_returns_accepted(), test_get_analysis_run_detail() (+3 more)

### Community 39 - "Community 39"
Cohesion: 0.29
Nodes (16): FindingCategory, build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner(), normalize_semgrep(), _normalize_severity() (+8 more)

### Community 40 - "Community 40"
Cohesion: 0.17
Nodes (15): DashboardBlockingCategory, DashboardFindingCount, DashboardOpenPullRequestAction, DashboardRecentAnalysisRun, DashboardSummaryRead, _calculate_approval_rate(), _enum_value(), get_dashboard_summary() (+7 more)

### Community 41 - "Community 41"
Cohesion: 0.21
Nodes (13): compiled_review_graph(), generate_ai_review_snapshot(), AIReviewError, AIReviewSkipped, build_invocation_config(), configure_langsmith_from_settings(), _load_example(), test_configure_langsmith_from_settings_copies_env() (+5 more)

### Community 42 - "Community 42"
Cohesion: 0.13
Nodes (16): _blocking_severities(), parse_json_output(), run_security_gate(), _scanner_commands(), test_blocking_severities_from_dict_and_list(), test_normalize_scanner_unknown_returns_empty(), test_normalize_severity_variants(), test_parse_json_output_invalid_json() (+8 more)

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (6): _post_login_redirect_url(), _request_for_url(), test_post_login_redirect_keeps_configured_frontend_origin_locally(), test_post_login_redirect_uses_callback_origin_on_vercel_host_mismatch(), test_post_login_redirect_uses_forwarded_https_origin_on_vercel_host_mismatch(), test_settings_ignore_blank_env_and_infer_vercel_production()

### Community 44 - "Community 44"
Cohesion: 0.19
Nodes (13): build_graph(), draft(), emit(), retrieve(), validate(), AIReviewGenerated, AIReviewState, test_graph_fail_coverage_passes_decision_lock_and_must_cite() (+5 more)

### Community 45 - "Community 45"
Cohesion: 0.18
Nodes (13): cleanup_expired_oauth_states(), consume_oauth_state(), create_oauth_state(), CreatedOAuthState, exchange_code_for_user(), _hash_oauth_value(), _oauth_state_is_valid(), upsert_user_from_github() (+5 more)

### Community 46 - "Community 46"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 47 - "Community 47"
Cohesion: 0.24
Nodes (8): _correct_draft(), load_evidence(), build_ai_review_input(), ChangedFileHunkArgs, redact_json_like(), redact_text(), test_redact_json_like_redacts_nested_patch_without_mutating_input(), test_redact_text_masks_github_tokens_private_keys_and_assignments()

### Community 48 - "Community 48"
Cohesion: 0.23
Nodes (12): execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), _run_pipeline(), _skipped_gate(), _insert_pending_run() (+4 more)

### Community 49 - "Community 49"
Cohesion: 0.14
Nodes (6): _archive_url(), _NoAuthOnRedirect, _remove_container(), test_remove_container_swallows_errors(), test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header()

### Community 50 - "Community 50"
Cohesion: 0.15
Nodes (4): get_me(), github_callback(), github_login(), logout()

### Community 51 - "Community 51"
Cohesion: 0.25
Nodes (15): _blocking_reasons(), build_final_report(), build_github_comment_body(), build_operational_error_report(), _list_section(), _pillar_section(), _snapshot_summary(), _string_list() (+7 more)

### Community 52 - "Community 52"
Cohesion: 0.16
Nodes (11): repository_clone_url(), _github_archive(), _github_response(), test_command_snapshot_redacts_clone_token(), test_download_repository_archive_extracts_checkout_without_git(), test_github_client_uses_provided_installation_token(), fake_get(), test_pull_request_context_maps_paginated_files_and_truncates_large_diff() (+3 more)

### Community 53 - "Community 53"
Cohesion: 0.13
Nodes (15): command, depends_on, ports, volumes, postgres, condition, services, backend (+7 more)

### Community 54 - "Community 54"
Cohesion: 0.20
Nodes (4): build_login_url(), registered_oauth_callback_url(), test_build_login_url_requires_client_id(), test_upsert_user_updates_existing_connection()

### Community 55 - "Community 55"
Cohesion: 0.14
Nodes (14): build, context, dockerfile, VITE_API_BASE_URL, build, depends_on, environment, ports (+6 more)

### Community 56 - "Community 56"
Cohesion: 0.23
Nodes (13): getCoverageExecutionConfig(), updateCoverageExecutionConfig(), updateQualityGateConfig(), RepositoryQualityGateConfigPage, RepositoryWorkspaceContext, coveragePreset(), RepositoryQualityGateConfigPage(), enablePullRequestPublication() (+5 more)

### Community 57 - "Community 57"
Cohesion: 0.31
Nodes (7): GateEvaluationMode, QualityGateConfig, QualityGateConfigRead, QualityGateConfigUpdate, get_quality_gate_config(), update_quality_gate_config(), test_quality_gate_config_missing()

### Community 58 - "Community 58"
Cohesion: 0.15
Nodes (13): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, interval, retries, test, timeout, environment (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.23
Nodes (7): decrypt_token(), encrypt_token(), _fernet(), generate_key(), test_token_crypto_round_trip(), test_token_crypto_requires_encryption_key(), test_exchange_code_for_user_success()

### Community 60 - "Community 60"
Cohesion: 0.29
Nodes (8): logout(), App(), AuthenticatedApp(), handleLogout(), HelpPage, react, react-dom, react-router-dom

### Community 61 - "Community 61"
Cohesion: 0.24
Nodes (9): _safe_env(), test_command_result_snapshot_redacts_output(), test_isolated_runner_does_not_pass_app_secrets_to_container(), test_redact_text_leaves_plain_text_untouched(), test_redact_text_masks_private_key_block(), test_redact_text_masks_tokens_and_clone_credentials(), test_safe_env_defaults_path_when_absent(), test_safe_env_does_not_leak_app_secrets() (+1 more)

### Community 62 - "Community 62"
Cohesion: 0.27
Nodes (8): getRepository(), listAnalysisRuns(), RepositoryDetailPage, RunTicker(), RunTickerProps, tickClass(), RepositoryDetailPage(), AnalysisRunSummary

### Community 63 - "Community 63"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 65 - "Community 65"
Cohesion: 0.20
Nodes (9): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, framework (+1 more)

### Community 66 - "Community 66"
Cohesion: 0.22
Nodes (5): _make_workspace_writable(), run_command(), test_make_workspace_writable_skips_os_errors(), test_run_command_success_and_writable_chmod_continue(), test_run_command_timeout()

### Community 67 - "Community 67"
Cohesion: 0.33
Nodes (5): client(), db_session(), repository(), reset_database(), _reset_public_schema()

### Community 68 - "Community 68"
Cohesion: 0.32
Nodes (4): get_install_url(), list_installations(), GitHubInstallationRead, GitHubInstallUrlRead

### Community 70 - "Community 70"
Cohesion: 0.38
Nodes (4): _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional()

### Community 75 - "Community 75"
Cohesion: 0.50
Nodes (3): database_health(), health(), readiness()

## Knowledge Gaps
- **5 isolated node(s):** `@types/node`, `@types/react`, `@types/react-dom`, `typescript`, `quality-gate-backend`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 489 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 21` to `Community 2`, `Community 3`, `Community 7`, `Community 10`, `Community 11`, `Community 12`, `Community 15`, `Community 22`, `Community 23`, `Community 27`, `Community 28`, `Community 34`, `Community 35`, `Community 37`, `Community 41`, `Community 43`, `Community 44`, `Community 45`, `Community 47`, `Community 48`, `Community 49`, `Community 54`, `Community 59`, `Community 66`, `Community 68`, `Community 71`, `Community 75`, `Community 78`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 67 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@types/node`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _5 weakly-connected nodes found - possible missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05574229691876751 - nodes in this community are weakly interconnected._
- **Why does `AnalysisRunStatus` connect `Community 14` to `Community 1`, `Community 3`, `Community 38`, `Community 39`, `Community 40`, `Community 41`, `Community 11`, `Community 12`, `Community 13`, `Community 15`, `Community 48`, `Community 18`, `Community 51`, `Community 23`, `Community 24`, `Community 25`, `Community 27`, `Community 28`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.05277777777777778 - nodes in this community are weakly interconnected._