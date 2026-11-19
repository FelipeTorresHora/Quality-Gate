# Graph Report - Quality-Gate  (2026-11-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1899 nodes · 5882 edges · 103 communities (78 shown, 25 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 595 edges (avg confidence: 0.93)
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
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 90
- Community 91
- Community 92
- Community 102

## God Nodes (most connected - your core abstractions)
1. `AnalysisRunStatus` - 96 edges
2. `AppError` - 90 edges
3. `AnalysisRun` - 85 edges
4. `get_settings()` - 80 edges
5. `FindingCategory` - 66 edges
6. `GateDecision` - 57 edges
7. `GitHubClient` - 51 edges
8. `Repository` - 50 edges
9. `AnalysisTriggerSource` - 50 edges
10. `Settings` - 47 edges

## Surprising Connections (you probably didn't know these)
- `test_manual_analyze_enqueues_pending_run()` --uses--> `AnalysisTriggerSource`  [INFERRED]
  backend/tests/test_manual_pr_analysis.py → backend/app/models/enums.py
- `prepare_context()` --calls--> `valid_lines_for_diff()`  [INFERRED]
  backend/app/services/agent/graph.py → backend/tests/test_langgraph_review.py
- `_FakeRun` --uses--> `AnalysisRunStatus`  [INFERRED]
  backend/tests/test_ai_review_graph.py → backend/app/models/enums.py
- `_FakeRun` --uses--> `GateDecision`  [INFERRED]
  backend/tests/test_ai_review_graph.py → backend/app/models/enums.py
- `AICoverageReview` --uses--> `FindingCategory`  [INFERRED]
  backend/app/services/agent/schemas.py → backend/app/models/enums.py

## Import Cycles
- 2-file cycle: `backend/app/db/base.py -> backend/app/models/analysis_finding.py -> backend/app/db/base.py`
- 2-file cycle: `backend/app/db/base.py -> backend/app/models/quality_gate_config.py -> backend/app/db/base.py`

## Communities (103 total, 25 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (36): parse_cobertura_xml(), parse_go_coverprofile(), parse_lcov(), flush(), calculate_total(), CoverageFile, CoverageReport, apply_coverage_policy() (+28 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (31): generate_ai_review_snapshot(), AICoverageReview, AIGateFinding, AIReviewError, AIReviewPartial, AIReviewSkipped, AISecurityReview, AITechDebtReview (+23 more)

### Community 2 - "Community 2"
Cohesion: 0.16
Nodes (35): GitHubAppInstallation, GitHubConnection, InstallationRepository, Repository, UserRepositoryAccess, User, deactivate_installation(), get_active_installation_for_repository() (+27 more)

### Community 3 - "Community 3"
Cohesion: 0.10
Nodes (31): compiled_review_graph(), parse_ai_review_snapshot(), _batch(), _digest(), _fake_run(), FakeChat, graph_cache(), _handler() (+23 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (25): Settings, validate_runtime_security_settings(), create_runner_workspace(), IsolatedRunnerWorkspace, RunnerError, RunnerWorkspace, test_production_rejects_default_session_secret(), test_settings_ignore_blank_env_and_infer_vercel_production() (+17 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (38): env, name, runs-on, services, steps, concurrency, cancel-in-progress, group (+30 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (17): coverage_ai(), await_structured(), build_chat_model(), call_structured(), cap_text(), line_allowed(), outcome(), pillar_error() (+9 more)

### Community 8 - "Community 8"
Cohesion: 0.23
Nodes (6): Base, CoverageExecutionConfig, TimestampMixin, UUIDPrimaryKeyMixin, OAuthState, UserSession

### Community 9 - "Community 9"
Cohesion: 0.17
Nodes (28): CoverageReportFormat, FindingCategory, FindingSeverity, FindingSource, AnalysisFindingRead, _blocking_severities(), build_security_snapshot(), normalize_bandit() (+20 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (36): environment, ALLOW_LOCAL_RUNNER_IN_PRODUCTION, API_HOST, API_PORT, APP_ENV, APP_NAME, AUTH_CALLBACK_URL, DATABASE_URL (+28 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (31): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+23 more)

### Community 12 - "Community 12"
Cohesion: 0.14
Nodes (22): AnalysisJob, claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), requeue_stale(), process_next_job() (+14 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (22): invoke_review_tools(), tracing_enabled(), run_coverage_gate(), test_invoke_review_tools_fallback_changed_file_without_blocking_hunks(), _fake_analysis_run(), test_allowed_file_paths_includes_string_changed_files(), test_compiled_review_graph_is_cached(), test_coverage_gate_requires_base_and_head_sha() (+14 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (17): download_repository_archive(), repository_clone_url(), RepositoryRef, test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths(), _github_archive(), _github_response(), test_download_repository_archive_extracts_checkout_without_git() (+9 more)

### Community 15 - "Community 15"
Cohesion: 0.12
Nodes (17): build_login_url(), cleanup_expired_oauth_states(), consume_oauth_state(), create_oauth_state(), CreatedOAuthState, exchange_code_for_user(), _hash_oauth_value(), _oauth_state_is_valid() (+9 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (23): _batch_dict(), _bounded(), build_graph(), build_review_graph(), build_review_graph_input(), _digest_dict(), draft(), emit() (+15 more)

### Community 17 - "Community 17"
Cohesion: 0.09
Nodes (19): _docker_run_command(), parse_repository_url(), redacted_command(), _remove_container(), run_command(), run_isolated_command(), _runner_resource_limits(), _validate_archive_members() (+11 more)

### Community 18 - "Community 18"
Cohesion: 0.13
Nodes (24): API_BASE_URL, ApiError, getCookieValue(), getCurrentUser(), getGitHubInstallUrl(), getGitHubLoginUrl(), getHealth(), getPullRequestContext() (+16 more)

### Community 19 - "Community 19"
Cohesion: 0.14
Nodes (15): analyze_pull_request(), get_pull_request_context(), get_repository(), list_pull_requests(), list_repositories(), RepositoryRead, expire_tags(), _get_cache() (+7 more)

### Community 20 - "Community 20"
Cohesion: 0.11
Nodes (26): getAnalysisRun(), getQualityGateConfig(), publishAnalysisRunToGitHub(), AnalysisDetailPage, AIReviewPanel(), AnalysisDetailPage(), handlePublish(), handleRetry() (+18 more)

### Community 21 - "Community 21"
Cohesion: 0.09
Nodes (22): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+14 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (14): _action_for_open_pull_request(), _snapshot_html_url(), _make_workspace_writable(), test_dashboard_action_helpers(), test_list_pull_requests_without_github_repo_id(), test_make_workspace_writable_skips_os_errors(), test_dashboard_action_fail_and_skip_none_action(), test_quality_gate_config_missing() (+6 more)

### Community 23 - "Community 23"
Cohesion: 0.24
Nodes (23): AnalysisRun, AnalysisTriggerSource, PullRequestContextRead, _build_pending_run(), _coerce_context(), _commit_new_run_or_reuse(), _create_or_reuse(), create_or_reuse_error_webhook_analysis_run() (+15 more)

### Community 24 - "Community 24"
Cohesion: 0.22
Nodes (24): AnalysisRunStatus, GateDecision, test_report_service_pass_summary_and_suggestions(), test_report_service_skipped_and_error_ai_review_paths(), _disable_github_publication(), _enable_github_publication(), _insert_run(), _open_pull_request() (+16 more)

### Community 25 - "Community 25"
Cohesion: 0.15
Nodes (11): ChangedFileSnapshot, GitHubClient, _map_changed_file(), _map_pull_request(), _map_pull_request_snapshot(), test_github_client_raise_for_response_variants(), test_map_pull_request(), _pull_request_context() (+3 more)

### Community 26 - "Community 26"
Cohesion: 0.10
Nodes (4): GateExecutionEvidenceWorkspace, PreparedRevision, test_base_coverage_skipped_when_no_drop_policy(), test_coverage_gate_runs_commands_in_configured_working_directory()

### Community 27 - "Community 27"
Cohesion: 0.21
Nodes (22): _create_run(), _execute(), _gate_result(), _set_publish_flags(), _stub_passing_gates(), test_disabled_publication_flags_skip_github_writes(), test_execute_aborts_when_total_time_budget_exceeded(), test_execute_marks_error_on_unexpected_exception() (+14 more)

### Community 28 - "Community 28"
Cohesion: 0.14
Nodes (18): analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), _python_complexity(), run_technical_debt_gate(), _suggestions(), validate_diff_evidence() (+10 more)

### Community 29 - "Community 29"
Cohesion: 0.19
Nodes (19): _assessment(), budget_exhausted(), build_snapshot(), context_budget_for(), dedupe_paths(), _dump(), _fallback_summary(), _finding_allowed() (+11 more)

### Community 30 - "Community 30"
Cohesion: 0.10
Nodes (17): CommandResult, test_evidence_workspace_missing_base_sha_and_reprepare_revision(), run(), test_run_revision_coverage_missing_report_and_parse_formats(), run(), test_run_security_gate_python_scanners_in_run_path(), run(), test_command_snapshot_redacts_clone_token() (+9 more)

### Community 31 - "Community 31"
Cohesion: 0.12
Nodes (14): app_error_handler(), AppError, generate_app_jwt(), generate_installation_token(), _private_key(), boom(), test_github_app_auth_private_key_path_and_errors(), test_github_app_auth_private_key_and_installation_token() (+6 more)

### Community 32 - "Community 32"
Cohesion: 0.22
Nodes (19): GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult, analysis_run_target_url(), _client_for_run(), _get_run(), publication_frontend_origin(), publish_analysis_run_to_github() (+11 more)

### Community 33 - "Community 33"
Cohesion: 0.26
Nodes (21): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+13 more)

### Community 34 - "Community 34"
Cohesion: 0.13
Nodes (17): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), collect_tool_results(), get_changed_file_hunk(), get_gate_summary() (+9 more)

### Community 35 - "Community 35"
Cohesion: 0.14
Nodes (18): getDashboardSummary(), DashboardPage, AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts() (+10 more)

### Community 36 - "Community 36"
Cohesion: 0.30
Nodes (4): get_current_user(), require_csrf_token(), get_settings(), get_db()

### Community 37 - "Community 37"
Cohesion: 0.14
Nodes (16): receive_github_webhook(), GitHubWebhookResult, _find_webhook_user(), _has_valid_signature(), _ignored(), _parse_payload(), process_github_webhook(), _process_installation_event() (+8 more)

### Community 38 - "Community 38"
Cohesion: 0.18
Nodes (18): _patch_context(), fake_context(), _post_webhook(), _pull_request_context(), _pull_request_payload(), _signed_headers(), test_pull_request_webhook_creates_pending_analysis_run(), test_pull_request_webhook_is_idempotent_for_same_repository_pr_and_head_sha() (+10 more)

### Community 39 - "Community 39"
Cohesion: 0.13
Nodes (17): analyzePullRequest(), executeAnalysisRun(), listPullRequests(), RepositoryAnalysisRunsPage, RepositoryPullRequestsPage, EmptyState(), EmptyStateProps, StatusBadge() (+9 more)

### Community 40 - "Community 40"
Cohesion: 0.18
Nodes (11): RepositoryCreate, build_coverage_execution_config(), get_coverage_execution_config(), update_coverage_execution_config(), create_repository(), list_repositories(), test_create_repository_integrity_error(), test_coverage_execution_config_not_found_and_invalid_format() (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.21
Nodes (11): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get_quality_gate_config(), update_quality_gate_config(), AnalysisRunDetail, AnalysisRunSummary (+3 more)

### Community 42 - "Community 42"
Cohesion: 0.10
Nodes (20): concurrency, cancel-in-progress, group, name, runs-on, steps, jobs, graph (+12 more)

### Community 43 - "Community 43"
Cohesion: 0.13
Nodes (5): get_me(), github_callback(), github_login(), logout(), CurrentUserRead

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (8): get_coverage_execution_config(), update_coverage_execution_config(), GateEvaluationMode, CoverageExecutionConfigRead, CoverageExecutionConfigUpdate, QualityGateConfigRead, QualityGateConfigUpdate, test_coverage_execution_config_rejects_blank_fields()

### Community 45 - "Community 45"
Cohesion: 0.19
Nodes (18): create_session(), _decode_session(), get_user_for_session(), _hash_token(), revoke_session(), _session_record_is_active(), validate_csrf_token(), test_create_session_returns_raw_cookie_once() (+10 more)

### Community 46 - "Community 46"
Cohesion: 0.18
Nodes (10): _insert_analysis_run(), _patch_pull_requests(), fake_list_pull_requests(), _pull_request(), test_list_pull_requests_batches_review_state_for_multiple_prs(), test_list_pull_requests_includes_not_run_review_state(), test_list_pull_requests_marks_different_head_sha_as_outdated(), test_list_pull_requests_marks_matching_head_sha_as_current() (+2 more)

### Community 47 - "Community 47"
Cohesion: 0.27
Nodes (13): DashboardBlockingCategory, DashboardFindingCount, DashboardOpenPullRequestAction, DashboardRecentAnalysisRun, DashboardSummaryRead, _calculate_approval_rate(), _enum_value(), get_dashboard_summary() (+5 more)

### Community 48 - "Community 48"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 49 - "Community 49"
Cohesion: 0.15
Nodes (5): _post_login_redirect_url(), _request_for_url(), test_post_login_redirect_keeps_configured_frontend_origin_locally(), test_post_login_redirect_uses_callback_origin_on_vercel_host_mismatch(), test_post_login_redirect_uses_forwarded_https_origin_on_vercel_host_mismatch()

### Community 50 - "Community 50"
Cohesion: 0.19
Nodes (7): _correct_draft(), build_ai_review_input(), ChangedFileHunkArgs, redact_json_like(), redact_text(), test_redact_json_like_redacts_nested_patch_without_mutating_input(), test_redact_text_masks_github_tokens_private_keys_and_assignments()

### Community 51 - "Community 51"
Cohesion: 0.16
Nodes (7): CoverageLanguage, map_github_language(), _sync_coverage_config(), test_map_github_language_known_and_fallback(), test_sync_go_repository_applies_go_coverprofile_defaults(), test_sync_javascript_repository_applies_npm_lcov_defaults(), test_sync_unknown_github_language_uses_unconfirmed_python_preset()

### Community 52 - "Community 52"
Cohesion: 0.17
Nodes (6): _archive_url(), _default_runner_adapter(), _github_archive_headers(), _NoAuthOnRedirect, test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header()

### Community 53 - "Community 53"
Cohesion: 0.13
Nodes (15): command, depends_on, ports, volumes, postgres, condition, services, backend (+7 more)

### Community 54 - "Community 54"
Cohesion: 0.33
Nodes (10): GitHubPullRequestRead, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, get_pull_request_review_state(), get_pull_request_review_states(), _review_state_for_pull_request(), test_pull_request_review_state_helpers() (+2 more)

### Community 55 - "Community 55"
Cohesion: 0.30
Nodes (13): _blocking_reasons(), build_final_report(), build_operational_error_report(), _list_section(), _pillar_section(), _snapshot_summary(), _string_list(), _suggestions() (+5 more)

### Community 56 - "Community 56"
Cohesion: 0.27
Nodes (8): GitHubPullRequestWithReviewState, get_repository_pull_request_context(), installation_client_for_repository(), list_repository_pull_requests(), get_quality_gate_config(), update_quality_gate_config(), get_repository(), test_get_repository_not_found()

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (14): build, context, dockerfile, VITE_API_BASE_URL, build, depends_on, environment, ports (+6 more)

### Community 58 - "Community 58"
Cohesion: 0.23
Nodes (13): getCoverageExecutionConfig(), updateCoverageExecutionConfig(), updateQualityGateConfig(), RepositoryQualityGateConfigPage, RepositoryWorkspaceContext, coveragePreset(), RepositoryQualityGateConfigPage(), enablePullRequestPublication() (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.40
Nodes (10): AnalysisFinding, execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), _run_pipeline(), _skipped_gate() (+2 more)

### Community 60 - "Community 60"
Cohesion: 0.15
Nodes (13): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, interval, retries, test, timeout, environment (+5 more)

### Community 61 - "Community 61"
Cohesion: 0.23
Nodes (7): decrypt_token(), encrypt_token(), _fernet(), generate_key(), test_token_crypto_round_trip(), test_token_crypto_requires_encryption_key(), test_exchange_code_for_user_success()

### Community 62 - "Community 62"
Cohesion: 0.24
Nodes (9): _create_run(), _set_publish_flags(), test_publish_commit_status_maps_decision(), test_publish_creates_marked_pull_request_comment(), fake_create(), test_publish_redacts_pull_request_comment_body(), test_publish_rejects_pending_run(), test_publish_skips_disabled_channels() (+1 more)

### Community 63 - "Community 63"
Cohesion: 0.29
Nodes (8): logout(), App(), AuthenticatedApp(), handleLogout(), HelpPage, react, react-dom, react-router-dom

### Community 64 - "Community 64"
Cohesion: 0.20
Nodes (3): QualityGateConfig, test_manual_analyze_enqueues_pending_run(), test_manual_analyze_uses_coverage_working_directory_for_nested_project()

### Community 65 - "Community 65"
Cohesion: 0.25
Nodes (7): AIReviewGenerated, _load_example(), test_graph_fail_coverage_passes_decision_lock_and_must_cite(), fake_draft(), test_graph_validation_failure_returns_ai_review_error(), fake_draft(), test_graph_draft_accepts_structured_and_dict_results()

### Community 66 - "Community 66"
Cohesion: 0.24
Nodes (9): _safe_env(), test_command_result_snapshot_redacts_output(), test_isolated_runner_does_not_pass_app_secrets_to_container(), test_redact_text_leaves_plain_text_untouched(), test_redact_text_masks_private_key_block(), test_redact_text_masks_tokens_and_clone_credentials(), test_safe_env_defaults_path_when_absent(), test_safe_env_does_not_leak_app_secrets() (+1 more)

### Community 67 - "Community 67"
Cohesion: 0.27
Nodes (8): getRepository(), listAnalysisRuns(), RepositoryDetailPage, RunTicker(), RunTickerProps, tickClass(), RepositoryDetailPage(), AnalysisRunSummary

### Community 68 - "Community 68"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 69 - "Community 69"
Cohesion: 0.31
Nodes (6): _insert_run(), test_admin_execute_enqueues_run_and_returns_accepted(), test_get_analysis_run_detail(), test_list_analysis_runs_cache_miss_stores_repository_payload(), test_list_analysis_runs_for_repository(), test_non_admin_cannot_execute_or_publish_analysis()

### Community 70 - "Community 70"
Cohesion: 0.20
Nodes (9): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, framework (+1 more)

### Community 72 - "Community 72"
Cohesion: 0.32
Nodes (4): get_install_url(), list_installations(), GitHubInstallationRead, GitHubInstallUrlRead

### Community 73 - "Community 73"
Cohesion: 0.25
Nodes (5): _get_paginated_github_resource(), _get_paginated_user_resource(), list_installation_repositories(), test_github_installation_pagination_error(), test_user_installation_resource_paginates_with_oauth_token()

### Community 74 - "Community 74"
Cohesion: 0.29
Nodes (6): _gate_result(), _insert_pending_run(), test_analysis_execution_timeout_after_each_gate(), test_run_pipeline_time_budget_checks_between_gates(), load_run(), timeout_after()

### Community 75 - "Community 75"
Cohesion: 0.33
Nodes (4): _ai_review_response_schema(), _AIReviewJsonSchema, _inline_json_schema(), resolve()

### Community 76 - "Community 76"
Cohesion: 0.29
Nodes (3): BatchInput, NodeOutcome, PillarDigest

### Community 77 - "Community 77"
Cohesion: 0.43
Nodes (4): clear_session_cookies(), CreatedSession, set_session_cookies(), test_cookie_policy_helper_sets_secure_flags()

### Community 78 - "Community 78"
Cohesion: 0.47
Nodes (4): _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional()

### Community 82 - "Community 82"
Cohesion: 0.50
Nodes (3): database_health(), health(), readiness()

## Knowledge Gaps
- **5 isolated node(s):** `quality-gate-backend`, `@types/node`, `@types/react`, `@types/react-dom`, `typescript`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 512 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 36` to `Community 1`, `Community 2`, `Community 5`, `Community 7`, `Community 8`, `Community 12`, `Community 13`, `Community 14`, `Community 15`, `Community 16`, `Community 17`, `Community 19`, `Community 22`, `Community 31`, `Community 32`, `Community 37`, `Community 38`, `Community 41`, `Community 44`, `Community 45`, `Community 52`, `Community 56`, `Community 59`, `Community 61`, `Community 72`, `Community 73`, `Community 77`, `Community 82`, `Community 90`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 67 INFERRED edges - model-reasoned connections that need verification._
- **What connects `quality-gate-backend`, `@types/node`, `@types/react` to the rest of the system?**
  _5 weakly-connected nodes found - possible missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.08521303258145363 - nodes in this community are weakly interconnected._
- **Why does `AppError` connect `Community 31` to `Community 1`, `Community 2`, `Community 3`, `Community 13`, `Community 15`, `Community 22`, `Community 23`, `Community 24`, `Community 25`, `Community 27`, `Community 32`, `Community 36`, `Community 37`, `Community 38`, `Community 40`, `Community 41`, `Community 56`, `Community 59`, `Community 61`, `Community 72`, `Community 73`, `Community 82`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.08636363636363636 - nodes in this community are weakly interconnected._