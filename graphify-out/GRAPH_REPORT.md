# Graph Report - Quality-Gate  (2026-11-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1815 nodes · 5605 edges · 88 communities (66 shown, 22 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 569 edges (avg confidence: 0.93)
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
- Community 71
- Community 72
- Community 73
- Community 77
- Community 87

## God Nodes (most connected - your core abstractions)
1. `AppError` - 91 edges
2. `AnalysisRunStatus` - 90 edges
3. `AnalysisRun` - 87 edges
4. `get_settings()` - 77 edges
5. `FindingCategory` - 65 edges
6. `GitHubClient` - 58 edges
7. `GateDecision` - 53 edges
8. `AnalysisTriggerSource` - 49 edges
9. `Repository` - 48 edges
10. `FindingSeverity` - 46 edges

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

## Communities (88 total, 22 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (37): GateExecutionEvidenceWorkspace, PreparedRevision, parse_cobertura_xml(), parse_go_coverprofile(), parse_lcov(), flush(), calculate_total(), CoverageFile (+29 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (23): get_me(), github_callback(), github_login(), logout(), CurrentUserRead, build_login_url(), cleanup_expired_oauth_states(), consume_oauth_state() (+15 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (37): AIReviewPartial, ContextBudgetMetadata, _ai_finding(), _create_run(), _FakeGitHubResponse, _generated_review(), _inline(), _publish() (+29 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (34): list_installations(), GitHubAppInstallation, GitHubConnection, InstallationRepository, UserRepositoryAccess, User, deactivate_installation(), get_active_installation_for_repository() (+26 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (24): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get_coverage_execution_config(), update_coverage_execution_config(), get_dashboard_summary(), get_quality_gate_config() (+16 more)

### Community 6 - "Community 6"
Cohesion: 0.17
Nodes (9): get_current_user(), require_csrf_token(), get_install_url(), get_settings(), get_db(), CoverageExecutionConfigRead, GitHubInstallationRead, GitHubInstallUrlRead (+1 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (17): AICoverageReview, AIGateFinding, AISecurityReview, AITechDebtReview, BatchReviewOutput, InlineComment, parse_ai_review_snapshot(), PillarInsights (+9 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (38): env, name, runs-on, services, steps, concurrency, cancel-in-progress, group (+30 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (16): CoverageExecutionConfig, CoverageLanguage, CoverageReportFormat, FindingSource, CoverageExecutionConfigUpdate, build_coverage_execution_config(), get_coverage_execution_config(), map_github_language() (+8 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (29): FindingSeverity, _blocking_severities(), build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner(), normalize_semgrep() (+21 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (36): environment, ALLOW_LOCAL_RUNNER_IN_PRODUCTION, API_HOST, API_PORT, APP_ENV, APP_NAME, AUTH_CALLBACK_URL, DATABASE_URL (+28 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (31): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+23 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (19): download_repository_archive(), _github_archive_headers(), repository_clone_url(), RepositoryRef, test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths(), _github_archive(), _github_response() (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.09
Nodes (20): database_health(), health(), readiness(), app_error_handler(), AppError, generate_app_jwt(), generate_installation_token(), _private_key() (+12 more)

### Community 15 - "Community 15"
Cohesion: 0.15
Nodes (27): AnalysisRun, AnalysisFindingRead, AnalysisRunDetail, AnalysisRunSummary, GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult, analysis_run_target_url() (+19 more)

### Community 16 - "Community 16"
Cohesion: 0.29
Nodes (7): Base, AnalysisFinding, AnalysisJob, TimestampMixin, UUIDPrimaryKeyMixin, OAuthState, UserSession

### Community 17 - "Community 17"
Cohesion: 0.18
Nodes (26): AnalysisRunStatus, GateDecision, test_build_ai_review_input_redacts_diff_changed_files_and_findings(), _FakeRun, test_report_service_pass_summary_and_suggestions(), test_report_service_skipped_and_error_ai_review_paths(), _disable_github_publication(), _enable_github_publication() (+18 more)

### Community 18 - "Community 18"
Cohesion: 0.14
Nodes (22): build_graph(), compiled_review_graph(), _correct_draft(), draft(), emit(), load_evidence(), retrieve(), validate() (+14 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (24): API_BASE_URL, ApiError, getCookieValue(), getCurrentUser(), getGitHubInstallUrl(), getGitHubLoginUrl(), getHealth(), getPullRequestContext() (+16 more)

### Community 20 - "Community 20"
Cohesion: 0.18
Nodes (25): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+17 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (18): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), ChangedFileHunkArgs, collect_tool_results(), get_changed_file_hunk() (+10 more)

### Community 22 - "Community 22"
Cohesion: 0.14
Nodes (21): claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), requeue_stale(), process_next_job(), run_forever() (+13 more)

### Community 23 - "Community 23"
Cohesion: 0.11
Nodes (26): getAnalysisRun(), getQualityGateConfig(), publishAnalysisRunToGitHub(), AnalysisDetailPage, AIReviewPanel(), AnalysisDetailPage(), handlePublish(), handleRetry() (+18 more)

### Community 24 - "Community 24"
Cohesion: 0.09
Nodes (22): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+14 more)

### Community 25 - "Community 25"
Cohesion: 0.10
Nodes (15): _post_login_redirect_url(), validate_runtime_security_settings(), decrypt_token(), encrypt_token(), _fernet(), generate_key(), _request_for_url(), test_post_login_redirect_keeps_configured_frontend_origin_locally() (+7 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (19): Repository, RepositoryCreate, create_repository(), get_repository_by_full_name(), list_repositories(), client(), create_user_repo_access(), create() (+11 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (11): IsolatedRunnerWorkspace, _make_workspace_writable(), _remove_container(), run_command(), test_make_workspace_writable_skips_os_errors(), test_remove_container_swallows_errors(), test_token_crypto_requires_encryption_key(), test_isolated_runner_workspace_paths() (+3 more)

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (17): invoke_review_tools(), tracing_enabled(), test_invoke_review_tools_fallback_changed_file_without_blocking_hunks(), _fake_analysis_run(), test_allowed_file_paths_includes_string_changed_files(), test_compiled_review_graph_is_cached(), test_decision_lock_requires_blocking_reasons_on_fail(), test_evaluate_review_runs_optional_evaluators() (+9 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (21): is_source_file(), analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), _python_complexity(), run_technical_debt_gate(), _suggestions() (+13 more)

### Community 30 - "Community 30"
Cohesion: 0.11
Nodes (14): Settings, create_runner_workspace(), _default_runner_adapter(), RunnerWorkspace, test_configure_langsmith_from_settings_copies_env(), test_runner_workspace_removes_existing_root(), test_runtime_cache_disabled_returns_none(), test_runtime_cache_get_cache_success_path() (+6 more)

### Community 31 - "Community 31"
Cohesion: 0.15
Nodes (19): _docker_run_command(), parse_repository_url(), run_isolated_command(), RunnerError, _validate_archive_members(), test_technical_debt_gate_missing_file_runner_error_and_suggestions(), prepare_head(), test_create_runner_workspace_unsupported_adapter() (+11 more)

### Community 32 - "Community 32"
Cohesion: 0.21
Nodes (22): _create_run(), _execute(), _gate_result(), _set_publish_flags(), _stub_passing_gates(), test_disabled_publication_flags_skip_github_writes(), test_execute_aborts_when_total_time_budget_exceeded(), test_execute_marks_error_on_unexpected_exception() (+14 more)

### Community 33 - "Community 33"
Cohesion: 0.14
Nodes (20): _patch_context(), fake_context(), _post_webhook(), _pull_request_context(), _pull_request_payload(), _signed_headers(), test_installation_webhook_dispatches_sync(), test_pull_request_webhook_creates_pending_analysis_run() (+12 more)

### Community 34 - "Community 34"
Cohesion: 0.13
Nodes (19): DashboardBlockingCategory, DashboardFindingCount, DashboardOpenPullRequestAction, DashboardRecentAnalysisRun, DashboardSummaryRead, _action_for_open_pull_request(), _calculate_approval_rate(), _enum_value() (+11 more)

### Community 35 - "Community 35"
Cohesion: 0.14
Nodes (22): clear_session_cookies(), create_session(), CreatedSession, _decode_session(), get_user_for_session(), _hash_token(), revoke_session(), _session_record_is_active() (+14 more)

### Community 36 - "Community 36"
Cohesion: 0.27
Nodes (18): AnalysisTriggerSource, PullRequestContextRead, _build_pending_run(), _coerce_context(), _commit_new_run_or_reuse(), _create_or_reuse(), create_or_reuse_error_webhook_analysis_run(), create_or_reuse_manual_analysis_run() (+10 more)

### Community 37 - "Community 37"
Cohesion: 0.20
Nodes (16): ChangedFileSnapshot, GitHubPullRequestRead, GitHubPullRequestWithReviewState, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, _map_changed_file(), _map_pull_request() (+8 more)

### Community 38 - "Community 38"
Cohesion: 0.11
Nodes (14): CommandResult, test_evidence_workspace_prepare_base_and_path_guard(), run(), test_evidence_workspace_missing_base_sha_and_reprepare_revision(), run(), test_run_revision_coverage_missing_report_and_parse_formats(), run(), test_run_security_gate_python_scanners_in_run_path() (+6 more)

### Community 39 - "Community 39"
Cohesion: 0.14
Nodes (18): getDashboardSummary(), DashboardPage, AlertsPanel(), InsightCards(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts() (+10 more)

### Community 40 - "Community 40"
Cohesion: 0.13
Nodes (17): analyzePullRequest(), executeAnalysisRun(), listPullRequests(), RepositoryAnalysisRunsPage, RepositoryPullRequestsPage, EmptyState(), EmptyStateProps, StatusBadge() (+9 more)

### Community 41 - "Community 41"
Cohesion: 0.15
Nodes (9): GateEvaluationMode, QualityGateConfig, QualityGateConfigRead, QualityGateConfigUpdate, get_quality_gate_config(), update_quality_gate_config(), test_quality_gate_config_missing(), test_manual_analyze_enqueues_pending_run() (+1 more)

### Community 42 - "Community 42"
Cohesion: 0.19
Nodes (20): _blocking_reasons(), build_final_report(), build_operational_error_report(), _code_review_section(), _context_budget_section(), _finding_label(), _insight_assessment(), _insight_lines() (+12 more)

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (20): concurrency, cancel-in-progress, group, name, runs-on, steps, jobs, graph (+12 more)

### Community 44 - "Community 44"
Cohesion: 0.18
Nodes (10): _insert_analysis_run(), _patch_pull_requests(), fake_list_pull_requests(), _pull_request(), test_list_pull_requests_batches_review_state_for_multiple_prs(), test_list_pull_requests_includes_not_run_review_state(), test_list_pull_requests_marks_different_head_sha_as_outdated(), test_list_pull_requests_marks_matching_head_sha_as_current() (+2 more)

### Community 45 - "Community 45"
Cohesion: 0.27
Nodes (3): GitHubClient, test_github_client_raise_for_response_variants(), test_github_client_requires_token_and_maps_endpoints()

### Community 46 - "Community 46"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 47 - "Community 47"
Cohesion: 0.22
Nodes (10): receive_github_webhook(), GitHubWebhookResult, _find_webhook_user(), _has_valid_signature(), _ignored(), process_github_webhook(), _process_installation_event(), _pull_request_snapshot_from_payload() (+2 more)

### Community 48 - "Community 48"
Cohesion: 0.16
Nodes (3): Runner, load_examples(), main()

### Community 49 - "Community 49"
Cohesion: 0.13
Nodes (15): command, depends_on, ports, volumes, postgres, condition, services, backend (+7 more)

### Community 50 - "Community 50"
Cohesion: 0.30
Nodes (10): execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), _run_pipeline(), _skipped_gate(), test_analysis_execution_reraises_app_error_and_missing_run() (+2 more)

### Community 51 - "Community 51"
Cohesion: 0.19
Nodes (12): redact_text(), redacted_command(), _safe_env(), test_command_result_snapshot_redacts_output(), test_isolated_runner_does_not_pass_app_secrets_to_container(), test_redact_text_leaves_plain_text_untouched(), test_redact_text_masks_private_key_block(), test_redact_text_masks_tokens_and_clone_credentials() (+4 more)

### Community 52 - "Community 52"
Cohesion: 0.18
Nodes (5): _archive_url(), _NoAuthOnRedirect, _runner_resource_limits(), test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header()

### Community 53 - "Community 53"
Cohesion: 0.13
Nodes (4): _BrokenCache, _FakeCache, test_get_cache_returns_none_when_runtime_cache_ctor_fails(), test_get_cache_returns_none_when_vercel_import_fails()

### Community 54 - "Community 54"
Cohesion: 0.14
Nodes (14): build, context, dockerfile, VITE_API_BASE_URL, build, depends_on, environment, ports (+6 more)

### Community 55 - "Community 55"
Cohesion: 0.23
Nodes (13): getCoverageExecutionConfig(), updateCoverageExecutionConfig(), updateQualityGateConfig(), RepositoryQualityGateConfigPage, RepositoryWorkspaceContext, coveragePreset(), RepositoryQualityGateConfigPage(), enablePullRequestPublication() (+5 more)

### Community 56 - "Community 56"
Cohesion: 0.22
Nodes (8): FindingCategory, GateResult, _gate_result(), _insert_pending_run(), test_analysis_execution_timeout_after_each_gate(), test_run_pipeline_time_budget_checks_between_gates(), load_run(), timeout_after()

### Community 57 - "Community 57"
Cohesion: 0.15
Nodes (13): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, interval, retries, test, timeout, environment (+5 more)

### Community 58 - "Community 58"
Cohesion: 0.29
Nodes (8): logout(), App(), AuthenticatedApp(), handleLogout(), HelpPage, react, react-dom, react-router-dom

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
Nodes (6): _insert_run(), test_admin_execute_enqueues_run_and_returns_accepted(), test_get_analysis_run_detail(), test_list_analysis_runs_cache_miss_stores_repository_payload(), test_list_analysis_runs_for_repository(), test_non_admin_cannot_execute_or_publish_analysis()

### Community 63 - "Community 63"
Cohesion: 0.20
Nodes (9): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, framework (+1 more)

### Community 64 - "Community 64"
Cohesion: 0.33
Nodes (4): _ai_review_response_schema(), _AIReviewJsonSchema, _inline_json_schema(), resolve()

### Community 65 - "Community 65"
Cohesion: 0.43
Nodes (5): get_repository_pull_request_context(), installation_client_for_repository(), list_repository_pull_requests(), get_repository(), test_list_pull_requests_without_github_repo_id()

### Community 72 - "Community 72"
Cohesion: 0.67
Nodes (3): _pull_request_context(), test_get_pull_request_context_maps_github_data_without_creating_run(), fake_context()

## Knowledge Gaps
- **5 isolated node(s):** `@types/node`, `@types/react`, `@types/react-dom`, `typescript`, `quality-gate-backend`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 489 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 6` to `Community 1`, `Community 3`, `Community 4`, `Community 13`, `Community 14`, `Community 15`, `Community 18`, `Community 25`, `Community 27`, `Community 28`, `Community 30`, `Community 31`, `Community 33`, `Community 35`, `Community 37`, `Community 47`, `Community 50`, `Community 52`, `Community 70`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 25 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@types/node`, `@types/react`, `@types/react-dom` to the rest of the system?**
  _5 weakly-connected nodes found - possible missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05765765765765766 - nodes in this community are weakly interconnected._
- **Why does `GateExecutionEvidenceWorkspace` connect `Community 0` to `Community 69`, `Community 38`, `Community 10`, `Community 15`, `Community 48`, `Community 50`, `Community 26`, `Community 29`, `Community 30`, `Community 31`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 62 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 62 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06140350877192982 - nodes in this community are weakly interconnected._