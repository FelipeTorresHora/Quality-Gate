# Graph Report - workspace  (2026-09-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1790 nodes · 5019 edges · 104 communities (77 shown, 27 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 602 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1c96999f`
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
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 99
- Community 100
- Community 101
- Community 103

## God Nodes (most connected - your core abstractions)
1. `get_settings()` - 75 edges
2. `AnalysisRunStatus` - 68 edges
3. `AppError` - 67 edges
4. `AnalysisRun` - 66 edges
5. `User` - 56 edges
6. `FindingCategory` - 50 edges
7. `GateDecision` - 42 edges
8. `Repository` - 41 edges
9. `Settings` - 41 edges
10. `GitHubClient` - 37 edges

## Surprising Connections (you probably didn't know these)
- `Architecture` --references--> `AnalysisRun`  [INFERRED]
  CLAUDE.md → backend/app/models/analysis_run.py
- `Architecture` --references--> `GitHubClient`  [INFERRED]
  CLAUDE.md → backend/app/services/github_service.py
- `Architecture` --references--> `ApiError`  [INFERRED]
  CLAUDE.md → frontend/src/api/client.ts
- `Architecture` --references--> `Settings`  [INFERRED]
  CLAUDE.md → backend/app/core/config.py
- `Architecture` --references--> `AnalysisRunStatus`  [INFERRED]
  CLAUDE.md → backend/app/models/enums.py

## Import Cycles
- None detected.

## Communities (104 total, 27 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (96): _post_login_redirect_url(), list_installations(), Session, Base, GitHubAppInstallation, GitHubConnection, InstallationRepository, TimestampMixin (+88 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (68): post, Request, Session, receive_github_webhook(), AnalysisRun, AnalysisTriggerSource, ChangedFileSnapshot, GitHubPullRequestRead (+60 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (72): AnalysisRunStatus, GateDecision, AnalysisFindingRead, AnalysisRunDetail, AnalysisRunSummary, GitHubPublicationCommentResult, GitHubPublicationResult, GitHubPublicationStatusResult (+64 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (42): parse_cobertura_xml(), Path, parse_go_coverprofile(), Path, parse_lcov(), flush(), Path, calculate_total() (+34 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (33): app_services_agent, app_services_agent_evaluators, app_services_agent_schemas, app_services_agent_tracing, Any, model_validator, _find_webhook_user(), _parse_payload() (+25 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (31): app_models_user, AppError, Exception, build_login_url(), cleanup_expired_oauth_states(), consume_oauth_state(), create_oauth_state(), CreatedOAuthState (+23 more)

### Community 6 - "Community 6"
Cohesion: 0.13
Nodes (37): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get, post, Session, UUID (+29 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (22): CoverageExecutionConfig, CoverageLanguage, CoverageReportFormat, CoverageExecutionConfigRead, CoverageExecutionConfigUpdate, BaseModel, model_validator, build_coverage_execution_config() (+14 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (3): alembic, collections_abc, sqlalchemy_dialects

### Community 9 - "Community 9"
Cohesion: 0.06
Nodes (32): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+24 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (25): AnalysisJob, claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), timedelta, UUID (+17 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (24): app_schemas_coverage_execution_config, app_schemas_github, app_services_agent_tools, app_services_pull_request_review_service, _gate_result(), _insert_pending_run(), test_analysis_execution_reraises_app_error_and_missing_run(), test_analysis_execution_timeout_after_each_gate() (+16 more)

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (27): getAnalysisRun(), getQualityGateConfig(), publishAnalysisRunToGitHub(), AnalysisDetailPage, AIReviewPanel(), AnalysisDetailPage(), handlePublish(), handleRetry() (+19 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (29): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), ChangedFileHunkArgs, collect_tool_results(), get_changed_file_hunk() (+21 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (23): API_BASE_URL, ApiError, getCookieValue(), getCurrentUser(), getGitHubInstallUrl(), getGitHubLoginUrl(), getHealth(), getPullRequestContext() (+15 more)

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (25): Settings, validate_runtime_security_settings(), tracing_enabled(), create_runner_workspace(), _default_runner_adapter(), RunnerWorkspace, test_configure_langsmith_from_settings_copies_env(), test_production_rejects_default_session_secret() (+17 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (21): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+13 more)

### Community 17 - "Community 17"
Cohesion: 0.19
Nodes (23): _create_run(), _execute(), _gate_result(), _set_publish_flags(), _stub_passing_gates(), test_disabled_publication_flags_skip_github_writes(), test_execute_aborts_when_total_time_budget_exceeded(), test_execute_marks_error_on_unexpected_exception() (+15 more)

### Community 18 - "Community 18"
Cohesion: 0.10
Nodes (7): GateExecutionEvidenceWorkspace, PreparedRevision, Path, test_evidence_workspace_prepare_base_and_path_guard(), run(), test_evidence_workspace_missing_base_sha_and_reprepare_revision(), run()

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 20 - "Community 20"
Cohesion: 0.14
Nodes (19): app_db_session, analysis_run_target_url(), publication_frontend_origin(), _create_run(), installation_token(), _raise_installation_token_error(), _set_publish_flags(), test_analysis_run_target_url_uses_frontend_origin_locally() (+11 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 23 - "Community 23"
Cohesion: 0.09
Nodes (20): app_core_errors, app_models_github_app_installation, app_models_installation_repository, app_models_repository, app_models_user_repository_access, app_schemas_repository, app_services_coverage_parsers_cobertura, app_services_coverage_parsers_types (+12 more)

### Community 24 - "Community 24"
Cohesion: 0.29
Nodes (20): FindingCategory, FindingSeverity, _blocking_severities(), build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner() (+12 more)

### Community 25 - "Community 25"
Cohesion: 0.26
Nodes (22): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+14 more)

### Community 26 - "Community 26"
Cohesion: 0.16
Nodes (18): _docker_run_command(), download_repository_archive(), _github_archive_headers(), _make_workspace_writable(), Exception, Path, _remove_container(), run_command() (+10 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (21): _patch_context(), fake_context(), _post_webhook(), _pull_request_context(), _pull_request_payload(), fixture, _signed_headers(), test_pull_request_webhook_creates_pending_analysis_run() (+13 more)

### Community 28 - "Community 28"
Cohesion: 0.13
Nodes (16): getDashboardSummary(), DashboardPage, AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts(), deriveInsights(), InsightTone (+8 more)

### Community 29 - "Community 29"
Cohesion: 0.26
Nodes (9): get_current_user(), app_error_handler(), Request, get_db(), Session, fastapi, fastapi_middleware_cors, fastapi_responses (+1 more)

### Community 30 - "Community 30"
Cohesion: 0.20
Nodes (19): build_graph(), _correct_draft(), draft(), emit(), load_evidence(), Any, retrieve(), validate() (+11 more)

### Community 31 - "Community 31"
Cohesion: 0.19
Nodes (21): AnalysisRun, app_models_analysis_run, app_schemas_analysis, app_services_github_service, app_services_report_service, _client_for_run(), _get_run(), publish_analysis_run_to_github() (+13 more)

### Community 32 - "Community 32"
Cohesion: 0.09
Nodes (16): app_models_enums, app_services_gates, app_services_runner_service, test_manual_analyze_enqueues_pending_run(), test_blocking_severities_from_dict_and_list(), test_normalize_scanner_unknown_returns_empty(), test_normalize_severity_variants(), test_parse_json_output_invalid_json() (+8 more)

### Community 33 - "Community 33"
Cohesion: 0.16
Nodes (21): Request, Session, require_csrf_token(), clear_session_cookies(), CreatedSession, _decode_session(), get_user_for_session(), _hash_token() (+13 more)

### Community 34 - "Community 34"
Cohesion: 0.13
Nodes (10): Runner, CommandResult, IsolatedRunnerWorkspace, test_isolated_runner_workspace_paths(), test_isolated_workspace_makes_tree_writable(), test_runner_workspace_checkout_and_run(), fake_download(), fake_run() (+2 more)

### Community 35 - "Community 35"
Cohesion: 0.20
Nodes (19): AST, is_source_file(), analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), Path, _python_complexity() (+11 more)

### Community 36 - "Community 36"
Cohesion: 0.20
Nodes (14): get_settings(), configure_langsmith_from_settings(), Copy LangSmith Settings onto process env before the review graph runs., generate_app_jwt(), generate_installation_token(), _private_key(), _get_paginated_user_resource(), test_github_app_auth_private_key_path_and_errors() (+6 more)

### Community 37 - "Community 37"
Cohesion: 0.19
Nodes (14): compiled_review_graph(), generate_ai_review_snapshot(), AIReviewError, AIReviewSkipped, BaseModel, build_invocation_config(), Any, _load_example() (+6 more)

### Community 38 - "Community 38"
Cohesion: 0.10
Nodes (18): CI, First-time setup (developer), Graphify, Graphify Cloud and GitHub PR reviews, Prerequisites, Project layout, Relationship to Quality Gate, AI Review (+10 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (12): parse_repository_url(), UUID, test_command_result_includes_adapter_and_limits(), test_docker_run_command_rejects_invalid_network(), test_parse_repository_url_extracts_token(), test_parse_repository_url_rejects_invalid_path(), test_parse_repository_url_rejects_non_github(), test_run_command_timeout() (+4 more)

### Community 40 - "Community 40"
Cohesion: 0.19
Nodes (14): executeAnalysisRun(), logout(), App(), AuthenticatedApp(), handleLogout(), HelpPage, RepositoryAnalysisRunsPage, PageFallback() (+6 more)

### Community 41 - "Community 41"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 42 - "Community 42"
Cohesion: 0.12
Nodes (6): app_core_config, app_services, _BrokenCache, _FakeCache, test_get_cache_returns_none_when_runtime_cache_ctor_fails(), test_get_cache_returns_none_when_vercel_import_fails()

### Community 43 - "Community 43"
Cohesion: 0.15
Nodes (12): repository_clone_url(), _github_archive(), _github_response(), test_command_snapshot_redacts_clone_token(), test_download_repository_archive_extracts_checkout_without_git(), test_github_client_uses_provided_installation_token(), fake_get(), test_pull_request_context_maps_paginated_files_and_truncates_large_diff() (+4 more)

### Community 44 - "Community 44"
Cohesion: 0.12
Nodes (6): RepositoryRef, test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths(), test_parse_repository_url_extracts_installation_token(), test_download_repository_archive_http_error(), test_download_repository_archive_success()

### Community 45 - "Community 45"
Cohesion: 0.16
Nodes (12): analyzePullRequest(), listPullRequests(), RepositoryPullRequestsPage, EmptyState(), EmptyStateProps, StatusBadge(), StatusBadgeProps, PullRequestTable() (+4 more)

### Community 46 - "Community 46"
Cohesion: 0.22
Nodes (14): get_quality_gate_config(), get, put, Session, UUID, update_quality_gate_config(), BaseModel, QualityGateConfigRead (+6 more)

### Community 47 - "Community 47"
Cohesion: 0.33
Nodes (12): AnalysisFinding, execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), Session, UUID (+4 more)

### Community 48 - "Community 48"
Cohesion: 0.19
Nodes (12): redact_text(), redacted_command(), _safe_env(), test_command_result_snapshot_redacts_output(), test_isolated_runner_does_not_pass_app_secrets_to_container(), test_redact_text_leaves_plain_text_untouched(), test_redact_text_masks_private_key_block(), test_redact_text_masks_tokens_and_clone_credentials() (+4 more)

### Community 49 - "Community 49"
Cohesion: 0.23
Nodes (13): getCoverageExecutionConfig(), updateCoverageExecutionConfig(), updateQualityGateConfig(), RepositoryQualityGateConfigPage, RepositoryWorkspaceContext, coveragePreset(), RepositoryQualityGateConfigPage(), enablePullRequestPublication() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.31
Nodes (7): build_ai_review_input(), Any, redact_json_like(), test_build_ai_review_input_redacts_diff_changed_files_and_findings(), test_redact_json_like_redacts_nested_patch_without_mutating_input(), test_redact_text_masks_github_tokens_private_keys_and_assignments(), re

### Community 51 - "Community 51"
Cohesion: 0.24
Nodes (9): load_examples(), main(), Push the git-versioned AI review golden dataset to LangSmith as qg-ai-…, _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional(), json (+1 more)

### Community 52 - "Community 52"
Cohesion: 0.25
Nodes (8): getRepository(), listAnalysisRuns(), RepositoryDetailPage, RunTicker(), RunTickerProps, tickClass(), RepositoryDetailPage(), AnalysisRunSummary

### Community 53 - "Community 53"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 54 - "Community 54"
Cohesion: 0.22
Nodes (8): get_install_url(), get, CurrentUserRead, BaseModel, GitHubInstallationRead, GitHubInstallUrlRead, BaseModel, pydantic

### Community 55 - "Community 55"
Cohesion: 0.31
Nodes (6): _insert_run(), test_admin_execute_enqueues_run_and_returns_accepted(), test_get_analysis_run_detail(), test_list_analysis_runs_cache_miss_stores_repository_payload(), test_list_analysis_runs_for_repository(), test_non_admin_cannot_execute_or_publish_analysis()

### Community 56 - "Community 56"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 57 - "Community 57"
Cohesion: 0.28
Nodes (9): get_me(), github_callback(), github_login(), logout(), get, post, Request, Response (+1 more)

### Community 58 - "Community 58"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 59 - "Community 59"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 60 - "Community 60"
Cohesion: 0.22
Nodes (8): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, routePrefix

### Community 61 - "Community 61"
Cohesion: 0.32
Nodes (6): _archive_url(), _NoAuthOnRedirect, test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header(), email_message, urllib_request

### Community 62 - "Community 62"
Cohesion: 0.29
Nodes (3): test_generate_app_jwt_requires_private_key(), test_installation_token_is_not_persisted(), pytest

### Community 63 - "Community 63"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 64 - "Community 64"
Cohesion: 0.33
Nodes (3): github_writes(), fake_list(), fixture

### Community 67 - "Community 67"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 68 - "Community 68"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 69 - "Community 69"
Cohesion: 0.50
Nodes (5): database_health(), health(), get, Session, readiness()

### Community 71 - "Community 71"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 72 - "Community 72"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### Community 73 - "Community 73"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 78 - "Community 78"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 79 - "Community 79"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 80 - "Community 80"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 81 - "Community 81"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 82 - "Community 82"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 83 - "Community 83"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **223 isolated node(s):** `ErrorMessageProps`, `LoadingBlockProps`, `RunStatusDonutProps`, `AnalysisFinding`, `AnalysisTriggerSource` (+218 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 578 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture` connect `Community 0` to `Community 1`, `Community 2`, `Community 36`, `Community 5`, `Community 12`, `Community 45`, `Community 14`, `Community 15`, `Community 52`, `Community 28`, `Community 29`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `Community 36` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 6`, `Community 15`, `Community 20`, `Community 26`, `Community 27`, `Community 29`, `Community 30`, `Community 31`, `Community 33`, `Community 37`, `Community 39`, `Community 46`, `Community 47`, `Community 54`, `Community 69`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `AnalysisRun` connect `Community 1` to `Community 0`, `Community 32`, `Community 2`, `Community 34`, `Community 36`, `Community 37`, `Community 10`, `Community 43`, `Community 47`, `Community 17`, `Community 50`, `Community 18`, `Community 55`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `get_settings()` (e.g. with `publication_frontend_origin()` and `_publish_commit_status()`) actually correct?**
  _`get_settings()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 45 inferred relationships involving `AnalysisRunStatus` (e.g. with `analyze_pull_request()` and `AnalysisRun`) actually correct?**
  _`AnalysisRunStatus` has 45 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `AnalysisRun` (e.g. with `AnalysisRunStatus` and `AnalysisTriggerSource`) actually correct?**
  _`AnalysisRun` has 35 INFERRED edges - model-reasoned connections that need verification._