# Graph Report - Quality-Gate  (2026-11-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2112 nodes · 6522 edges · 91 communities (71 shown, 20 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 560 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0435cebe`
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
- Community 74
- Community 75
- Community 77
- Community 78
- Community 80
- Community 90

## God Nodes (most connected - your core abstractions)
1. `AppError` - 95 edges
2. `AnalysisRun` - 90 edges
3. `AnalysisRunStatus` - 83 edges
4. `get_settings()` - 83 edges
5. `GitHubClient` - 58 edges
6. `FindingCategory` - 57 edges
7. `GateDecision` - 54 edges
8. `Settings` - 49 edges
9. `AnalysisTriggerSource` - 48 edges
10. `Repository` - 47 edges

## Surprising Connections (you probably didn't know these)
- `test_manual_analyze_enqueues_pending_run()` --uses--> `AnalysisTriggerSource`  [INFERRED]
  backend/tests/test_manual_pr_analysis.py → backend/app/models/enums.py
- `test_phase0_review_contracts_round_trip()` --uses--> `AnalysisRunDetail`  [INFERRED]
  backend/tests/test_ai_review_graph.py → backend/app/schemas/analysis.py
- `list_analysis_runs()` --uses--> `AnalysisRunSummary`  [INFERRED]
  backend/app/api/routes_analysis.py → backend/app/schemas/analysis.py
- `AnalysisRunSummary` --uses--> `AnalysisRunStatus`  [INFERRED]
  backend/app/schemas/analysis.py → backend/app/models/enums.py
- `AnalysisRunSummary` --uses--> `AnalysisTriggerSource`  [INFERRED]
  backend/app/schemas/analysis.py → backend/app/models/enums.py

## Import Cycles
- 2-file cycle: `backend/app/db/base.py -> backend/app/models/analysis_finding.py -> backend/app/db/base.py`
- 2-file cycle: `backend/app/db/base.py -> backend/app/models/quality_gate_config.py -> backend/app/db/base.py`

## Communities (91 total, 20 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (43): FindingSource, _ai_review_response_schema(), _AIReviewJsonSchema, AnalysisFindingRead, AnalysisRunDetail, AnalysisRunSummary, GitHubPublicationCommentResult, GitHubPublicationResult (+35 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (42): _create_run(), _execute(), _finding_rows(), _gate_result(), github_writes(), fake_list(), _record_container_gates(), wrap() (+34 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (50): _alert_paths(), _as_text(), _block(), _bound_sections(), build_coverage_digest(), build_debt_digest(), build_security_digest(), selected() (+42 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (26): build_review_graph(), merge_and_validate(), coverage_ai(), await_structured(), build_chat_model(), call_structured(), line_allowed(), outcome() (+18 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (42): parse_cobertura_xml(), parse_go_coverprofile(), _span_lines(), parse_lcov(), flush(), calculate_total(), CoverageFile, CoverageReport (+34 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (25): AICoverageReview, AIGateFinding, AISecurityReview, AITechDebtReview, BatchReviewOutput, InlineComment, PillarInsights, _require_finding_category() (+17 more)

### Community 6 - "Community 6"
Cohesion: 0.13
Nodes (39): FindingCategory, FindingSeverity, _blocking_severities(), build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner() (+31 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (30): compiled_review_graph(), parse_ai_review_snapshot(), _batch(), _digest(), _fake_run(), FakeChat, graph_cache(), _handler() (+22 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (30): AIReviewPartial, ContextBudgetMetadata, _ai_finding(), _create_run(), _generated_review(), _inline(), _publish(), _raise_installation_token_error() (+22 more)

### Community 10 - "Community 10"
Cohesion: 0.16
Nodes (32): GitHubAppInstallation, GitHubConnection, InstallationRepository, UserRepositoryAccess, User, deactivate_installation(), get_active_installation_for_repository(), _get_paginated_github_resource() (+24 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (32): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+24 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (38): env, name, runs-on, services, steps, concurrency, cancel-in-progress, group (+30 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (37): publishAnalysisRunToGitHub(), EmptyState(), StatusBadge(), AIGateFindingItem(), AIReviewPanel(), AnalysisDetailPage(), handlePublish(), arrayValue() (+29 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (23): Settings, validate_runtime_security_settings(), tracing_enabled(), Runner, create_runner_workspace(), _default_runner_adapter(), RunnerWorkspace, test_configure_langsmith_from_settings_copies_env() (+15 more)

### Community 15 - "Community 15"
Cohesion: 0.08
Nodes (7): GateExecutionEvidenceWorkspace, PreparedRevision, run_coverage_gate(), test_base_coverage_skipped_when_no_drop_policy(), test_coverage_gate_runs_commands_in_configured_working_directory(), test_coverage_gate_requires_base_and_head_sha(), test_security_gate_uses_repository_token_for_clone()

### Community 16 - "Community 16"
Cohesion: 0.07
Nodes (19): download_repository_archive(), _github_archive_headers(), repository_clone_url(), RepositoryRef, test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths(), _github_archive(), _github_response() (+11 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (36): environment, ALLOW_LOCAL_RUNNER_IN_PRODUCTION, API_HOST, API_PORT, APP_ENV, APP_NAME, AUTH_CALLBACK_URL, DATABASE_URL (+28 more)

### Community 18 - "Community 18"
Cohesion: 0.06
Nodes (31): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+23 more)

### Community 19 - "Community 19"
Cohesion: 0.11
Nodes (22): _docker_run_command(), parse_repository_url(), redacted_command(), run_command(), run_isolated_command(), RunnerError, _validate_archive_members(), test_technical_debt_gate_missing_file_runner_error_and_suggestions() (+14 more)

### Community 20 - "Community 20"
Cohesion: 0.11
Nodes (30): API_BASE_URL, ApiError, getAnalysisRun(), getCookieValue(), getCoverageExecutionConfig(), getCurrentUser(), getGitHubLoginUrl(), getHealth() (+22 more)

### Community 21 - "Community 21"
Cohesion: 0.28
Nodes (6): Base, AnalysisFinding, TimestampMixin, UUIDPrimaryKeyMixin, OAuthState, UserSession

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (16): CoverageExecutionConfig, CoverageLanguage, CoverageReportFormat, CoverageExecutionConfigRead, CoverageExecutionConfigUpdate, build_coverage_execution_config(), get_coverage_execution_config(), map_github_language() (+8 more)

### Community 23 - "Community 23"
Cohesion: 0.18
Nodes (27): AnalysisRunStatus, GateDecision, test_build_ai_review_input_redacts_diff_changed_files_and_findings(), test_report_service_pass_summary_and_suggestions(), _insert_pending_run(), test_analysis_execution_handles_unexpected_exception(), test_report_service_skipped_and_error_ai_review_paths(), _disable_github_publication() (+19 more)

### Community 24 - "Community 24"
Cohesion: 0.15
Nodes (24): _batch_dict(), _bounded(), build_graph(), build_review_graph_input(), _correct_draft(), _digest_dict(), draft(), emit() (+16 more)

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (16): get_dashboard_summary(), analyze_pull_request(), get_pull_request_context(), get_repository(), list_pull_requests(), list_repositories(), RepositoryRead, expire_tags() (+8 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (21): _accepted_score(), _add_ai_finding(), _ai_comment_payload(), _ai_finding_payload(), _attach_ai_review(), execute_analysis_run(), _expire_analysis_caches(), _finding_category() (+13 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (5): get_current_user(), require_csrf_token(), app_error_handler(), get_db(), configure_langsmith_from_settings()

### Community 28 - "Community 28"
Cohesion: 0.12
Nodes (18): database_health(), health(), readiness(), get_settings(), AppError, generate_app_jwt(), generate_installation_token(), _private_key() (+10 more)

### Community 29 - "Community 29"
Cohesion: 0.07
Nodes (17): invoke_review_tools(), test_invoke_review_tools_fallback_changed_file_without_blocking_hunks(), _fake_analysis_run(), test_allowed_file_paths_includes_string_changed_files(), test_compiled_review_graph_is_cached(), test_coverage_gate_is_source_file_branches(), test_decision_lock_requires_blocking_reasons_on_fail(), test_evaluate_review_runs_optional_evaluators() (+9 more)

### Community 30 - "Community 30"
Cohesion: 0.16
Nodes (22): AnalysisJob, claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), requeue_stale(), process_next_job() (+14 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (22): clear_session_cookies(), create_session(), CreatedSession, _decode_session(), get_user_for_session(), _hash_token(), revoke_session(), _session_record_is_active() (+14 more)

### Community 32 - "Community 32"
Cohesion: 0.12
Nodes (18): build_ai_review_input(), generate_ai_review_snapshot(), AIReviewError, AIReviewGenerated, AIReviewSkipped, build_invocation_config(), _load_ai_snapshot(), _FakeRun (+10 more)

### Community 33 - "Community 33"
Cohesion: 0.09
Nodes (19): CommandResult, run(), test_evidence_workspace_prepare_base_and_path_guard(), run(), test_run_revision_coverage_missing_report_and_parse_formats(), run(), test_run_security_gate_python_scanners_in_run_path(), run() (+11 more)

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (20): ChangedFileSnapshot, GitHubPullRequestRead, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, get_pull_request_review_state(), get_pull_request_review_states(), _review_state_for_pull_request() (+12 more)

### Community 35 - "Community 35"
Cohesion: 0.16
Nodes (26): AnalysisRun, _blocking_reasons(), build_final_report(), build_github_comment_body(), build_operational_error_report(), _code_review_section(), _context_budget_section(), _finding_label() (+18 more)

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (18): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), ChangedFileHunkArgs, collect_tool_results(), get_changed_file_hunk() (+10 more)

### Community 37 - "Community 37"
Cohesion: 0.12
Nodes (21): getGitHubInstallUrl(), listGitHubInstallations(), listRepositories(), logout(), AnalysisDetailPage, App(), AuthenticatedApp(), handleLogout() (+13 more)

### Community 38 - "Community 38"
Cohesion: 0.23
Nodes (21): AnalysisTriggerSource, GitHubWebhookResult, PullRequestContextRead, _build_pending_run(), _coerce_context(), _commit_new_run_or_reuse(), _create_or_reuse(), create_or_reuse_error_webhook_analysis_run() (+13 more)

### Community 39 - "Community 39"
Cohesion: 0.17
Nodes (11): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get_coverage_execution_config(), update_coverage_execution_config(), get_quality_gate_config(), update_quality_gate_config() (+3 more)

### Community 40 - "Community 40"
Cohesion: 0.16
Nodes (20): _patch_context(), fake_context(), _post_webhook(), _pull_request_context(), _pull_request_payload(), _signed_headers(), test_installation_webhook_dispatches_sync(), test_pull_request_webhook_creates_pending_analysis_run() (+12 more)

### Community 41 - "Community 41"
Cohesion: 0.14
Nodes (18): DashboardBlockingCategory, DashboardFindingCount, DashboardOpenPullRequestAction, DashboardRecentAnalysisRun, DashboardSummaryRead, _action_for_open_pull_request(), _calculate_approval_rate(), _enum_value() (+10 more)

### Community 42 - "Community 42"
Cohesion: 0.26
Nodes (21): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+13 more)

### Community 43 - "Community 43"
Cohesion: 0.22
Nodes (17): _assessment(), budget_exhausted(), build_snapshot(), context_budget_for(), dedupe_paths(), _dump(), _fallback_summary(), _finding_allowed() (+9 more)

### Community 44 - "Community 44"
Cohesion: 0.14
Nodes (18): getDashboardSummary(), DashboardPage, AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts() (+10 more)

### Community 45 - "Community 45"
Cohesion: 0.17
Nodes (14): build_login_url(), cleanup_expired_oauth_states(), consume_oauth_state(), create_oauth_state(), CreatedOAuthState, exchange_code_for_user(), _hash_oauth_value(), _oauth_state_is_valid() (+6 more)

### Community 46 - "Community 46"
Cohesion: 0.14
Nodes (17): executeAnalysisRun(), getRepository(), listAnalysisRuns(), RepositoryAnalysisRunsPage, RepositoryDetailPage, ErrorMessage(), ErrorMessageProps, RunTicker() (+9 more)

### Community 47 - "Community 47"
Cohesion: 0.21
Nodes (14): Repository, RepositoryCreate, create_repository(), get_repository(), get_repository_by_full_name(), list_repositories(), list_repositories_for_user(), test_create_repository_integrity_error() (+6 more)

### Community 48 - "Community 48"
Cohesion: 0.10
Nodes (20): concurrency, cancel-in-progress, group, name, runs-on, steps, jobs, graph (+12 more)

### Community 49 - "Community 49"
Cohesion: 0.13
Nodes (5): get_me(), github_callback(), github_login(), logout(), CurrentUserRead

### Community 50 - "Community 50"
Cohesion: 0.18
Nodes (10): _insert_analysis_run(), _patch_pull_requests(), fake_list_pull_requests(), _pull_request(), test_list_pull_requests_batches_review_state_for_multiple_prs(), test_list_pull_requests_includes_not_run_review_state(), test_list_pull_requests_marks_different_head_sha_as_outdated(), test_list_pull_requests_marks_matching_head_sha_as_current() (+2 more)

### Community 51 - "Community 51"
Cohesion: 0.18
Nodes (13): redact_json_like(), redact_text(), _safe_env(), test_redact_json_like_redacts_nested_patch_without_mutating_input(), test_redact_text_masks_github_tokens_private_keys_and_assignments(), test_command_result_snapshot_redacts_output(), test_isolated_runner_does_not_pass_app_secrets_to_container(), test_redact_text_leaves_plain_text_untouched() (+5 more)

### Community 52 - "Community 52"
Cohesion: 0.13
Nodes (7): _archive_url(), _NoAuthOnRedirect, _remove_container(), _runner_resource_limits(), test_remove_container_swallows_errors(), test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header()

### Community 53 - "Community 53"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 54 - "Community 54"
Cohesion: 0.15
Nodes (5): _post_login_redirect_url(), _request_for_url(), test_post_login_redirect_keeps_configured_frontend_origin_locally(), test_post_login_redirect_uses_callback_origin_on_vercel_host_mismatch(), test_post_login_redirect_uses_forwarded_https_origin_on_vercel_host_mismatch()

### Community 55 - "Community 55"
Cohesion: 0.10
Nodes (4): test_technical_debt_gate_python_and_brace_paths(), test_technical_debt_gate_syntax_error_returns_error(), test_manual_analyze_enqueues_pending_run(), test_manual_analyze_uses_coverage_working_directory_for_nested_project()

### Community 56 - "Community 56"
Cohesion: 0.13
Nodes (15): command, depends_on, ports, volumes, postgres, condition, services, backend (+7 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (14): build, context, dockerfile, VITE_API_BASE_URL, build, depends_on, environment, ports (+6 more)

### Community 58 - "Community 58"
Cohesion: 0.19
Nodes (10): analyzePullRequest(), listPullRequests(), RepositoryPullRequestsPage, EmptyStateProps, RepositoryWorkspaceContext, PullRequestTable(), RepositoryPullRequestsPage(), analyze() (+2 more)

### Community 59 - "Community 59"
Cohesion: 0.31
Nodes (7): GateEvaluationMode, QualityGateConfig, QualityGateConfigRead, QualityGateConfigUpdate, get_quality_gate_config(), update_quality_gate_config(), test_quality_gate_config_missing()

### Community 60 - "Community 60"
Cohesion: 0.18
Nodes (6): _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional(), test_generate_app_jwt_requires_private_key(), test_installation_token_is_not_persisted()

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (13): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, interval, retries, test, timeout, environment (+5 more)

### Community 62 - "Community 62"
Cohesion: 0.17
Nodes (5): IsolatedRunnerWorkspace, _make_workspace_writable(), test_make_workspace_writable_skips_os_errors(), test_isolated_runner_workspace_paths(), test_run_command_success_and_writable_chmod_continue()

### Community 63 - "Community 63"
Cohesion: 0.23
Nodes (7): decrypt_token(), encrypt_token(), _fernet(), generate_key(), test_token_crypto_round_trip(), test_token_crypto_requires_encryption_key(), test_exchange_code_for_user_success()

### Community 64 - "Community 64"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 65 - "Community 65"
Cohesion: 0.33
Nodes (7): client(), create_user_repo_access(), create(), db_session(), repository(), reset_database(), _reset_public_schema()

### Community 66 - "Community 66"
Cohesion: 0.31
Nodes (6): _insert_run(), test_admin_execute_enqueues_run_and_returns_accepted(), test_get_analysis_run_detail(), test_list_analysis_runs_cache_miss_stores_repository_payload(), test_list_analysis_runs_for_repository(), test_non_admin_cannot_execute_or_publish_analysis()

### Community 67 - "Community 67"
Cohesion: 0.20
Nodes (9): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, framework (+1 more)

### Community 68 - "Community 68"
Cohesion: 0.22
Nodes (3): test_exchange_code_for_user_handles_token_errors(), test_exchange_code_for_user_missing_access_token(), test_upsert_user_updates_existing_connection()

### Community 69 - "Community 69"
Cohesion: 0.32
Nodes (4): get_install_url(), list_installations(), GitHubInstallationRead, GitHubInstallUrlRead

### Community 70 - "Community 70"
Cohesion: 0.38
Nodes (5): _find_webhook_user(), _process_installation_event(), _pull_request_snapshot_from_payload(), test_webhook_find_user_without_sender(), test_webhook_installation_branches()

### Community 71 - "Community 71"
Cohesion: 0.67
Nodes (4): GitHubPullRequestWithReviewState, get_repository_pull_request_context(), installation_client_for_repository(), list_repository_pull_requests()

## Knowledge Gaps
- **5 isolated node(s):** `@types/node`, `@types/react`, `@types/react-dom`, `typescript`, `quality-gate-backend`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 554 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 28` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 10`, `Community 14`, `Community 16`, `Community 19`, `Community 24`, `Community 25`, `Community 26`, `Community 27`, `Community 29`, `Community 31`, `Community 32`, `Community 38`, `Community 39`, `Community 40`, `Community 45`, `Community 52`, `Community 62`, `Community 63`, `Community 69`, `Community 71`, `Community 76`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@types/node`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _5 weakly-connected nodes found - possible missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.056943056943056944 - nodes in this community are weakly interconnected._
- **Why does `AppError` connect `Community 28` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 7`, `Community 9`, `Community 10`, `Community 22`, `Community 23`, `Community 26`, `Community 27`, `Community 29`, `Community 31`, `Community 34`, `Community 35`, `Community 38`, `Community 39`, `Community 40`, `Community 45`, `Community 47`, `Community 59`, `Community 63`, `Community 69`, `Community 71`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `AnalysisRun` (e.g. with `AnalysisRunStatus` and `AnalysisTriggerSource`) actually correct?**
  _`AnalysisRun` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06923076923076923 - nodes in this community are weakly interconnected._