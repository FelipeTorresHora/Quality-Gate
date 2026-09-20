# Graph Report - workspace  (2026-09-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1801 nodes · 4980 edges · 100 communities (73 shown, 27 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 581 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fa6cde80`
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
- Community 87
- Community 88
- Community 89
- Community 90
- Community 95
- Community 96
- Community 97
- Community 99

## God Nodes (most connected - your core abstractions)
1. `AnalysisRun` - 83 edges
2. `get_settings()` - 72 edges
3. `AnalysisRunStatus` - 71 edges
4. `AppError` - 67 edges
5. `FindingCategory` - 50 edges
6. `GitHubClient` - 48 edges
7. `GateDecision` - 47 edges
8. `Settings` - 41 edges
9. `AnalysisTriggerSource` - 38 edges
10. `FindingSeverity` - 34 edges

## Surprising Connections (you probably didn't know these)
- `Architecture` --references--> `AnalysisRun`  [INFERRED]
  CLAUDE.md → backend/app/models/analysis_run.py
- `Architecture` --references--> `AnalysisRunStatus`  [INFERRED]
  CLAUDE.md → backend/app/models/enums.py
- `Architecture` --references--> `GateDecision`  [INFERRED]
  CLAUDE.md → backend/app/models/enums.py
- `Architecture` --references--> `Settings`  [INFERRED]
  CLAUDE.md → backend/app/core/config.py
- `Architecture` --references--> `GitHubClient`  [INFERRED]
  CLAUDE.md → backend/app/services/github_service.py

## Import Cycles
- None detected.

## Communities (100 total, 27 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (95): _post_login_redirect_url(), list_installations(), get, Session, Base, AnalysisFinding, GitHubAppInstallation, GitHubConnection (+87 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (90): AnalysisRun, AnalysisRunStatus, AnalysisTriggerSource, GateDecision, AnalysisFindingRead, AnalysisRunDetail, AnalysisRunSummary, GitHubPublicationCommentResult (+82 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (58): ChangedFileSnapshot, GitHubPullRequestRead, GitHubPullRequestWithReviewState, GitHubWebhookResult, PullRequestReviewRun, PullRequestReviewState, PullRequestSnapshot, BaseModel (+50 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (45): parse_cobertura_xml(), Path, parse_go_coverprofile(), Path, parse_lcov(), flush(), Path, calculate_total() (+37 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (37): app_models_analysis_run, app_models_github_app_installation, app_schemas_coverage_execution_config, app_services_agent_tools, app_services_coverage_parsers_cobertura, app_services_coverage_parsers_types, app_services_dashboard_service, app_services_gates (+29 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (23): CoverageExecutionConfig, CoverageLanguage, CoverageReportFormat, CoverageExecutionConfigRead, CoverageExecutionConfigUpdate, BaseModel, model_validator, build_coverage_execution_config() (+15 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (3): alembic, collections_abc, sqlalchemy_dialects

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (28): app_api_deps, app_schemas_analysis, app_services_session_service, AuthenticatedUser, get_dashboard_summary(), get, Session, analyze_pull_request() (+20 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (31): dependencies, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test, @types/node (+23 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (20): database_health(), health(), get, Session, readiness(), app_error_handler(), AppError, Exception (+12 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (24): _create_run(), _execute(), _gate_result(), _set_publish_flags(), _stub_passing_gates(), test_disabled_publication_flags_skip_github_writes(), test_execute_aborts_when_total_time_budget_exceeded(), test_execute_marks_error_on_unexpected_exception() (+16 more)

### Community 11 - "Community 11"
Cohesion: 0.23
Nodes (16): get_current_user(), Request, Session, require_csrf_token(), get_install_url(), get_settings(), get_db(), Session (+8 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (27): Any, model_validator, Settings, validate_runtime_security_settings(), tracing_enabled(), create_runner_workspace(), _default_runner_adapter(), RunnerWorkspace (+19 more)

### Community 13 - "Community 13"
Cohesion: 0.07
Nodes (18): Runner, CommandResult, test_evidence_workspace_missing_base_sha_and_reprepare_revision(), run(), test_run_security_gate_python_scanners_in_run_path(), run(), test_isolated_workspace_makes_tree_writable(), test_runner_workspace_checkout_and_run() (+10 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (18): download_repository_archive(), _github_archive_headers(), parse_repository_url(), UUID, RepositoryRef, _validate_archive_members(), test_download_archive_bad_layout(), test_download_archive_reuses_existing_paths() (+10 more)

### Community 15 - "Community 15"
Cohesion: 0.15
Nodes (25): AnalysisJob, claim_next(), ClaimedAnalysisJob, complete(), enqueue(), fail(), timedelta, UUID (+17 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (23): chartColors, SEVERITY_COLOR, SEVERITY_ORDER, RunStatusDonutProps, STATUS_COLOR, FindingsBar, RunStatusDonut, ScoreSparkline (+15 more)

### Community 17 - "Community 17"
Cohesion: 0.10
Nodes (29): build_review_tools(), _coverage(), _findings(), _hunk(), _summary(), collect_tool_results(), get_changed_file_hunk(), get_gate_summary() (+21 more)

### Community 18 - "Community 18"
Cohesion: 0.12
Nodes (25): getAnalysisRun(), publishAnalysisRunToGitHub(), AIReviewPanel(), AnalysisDetailPage(), handlePublish(), arrayValue(), displayValue(), formatDate() (+17 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (18): app_db_session, app_services_agent, app_services_agent_evaluators, app_services_agent_schemas, app_services_agent_tracing, app_services_report_service, _insert_pending_run(), test_allowed_file_paths_includes_string_changed_files() (+10 more)

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (26): get_me(), github_callback(), github_login(), logout(), get, post, Request, Response (+18 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (25): Any, app_models_enums, app_schemas_github, app_services_repository_service, post, Request, Session, receive_github_webhook() (+17 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (8): GateExecutionEvidenceWorkspace, PreparedRevision, Path, Exception, RunnerError, test_technical_debt_gate_missing_file_runner_error_and_suggestions(), prepare_head(), test_security_gate_uses_repository_token_for_clone()

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native AGENTS.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (19): ApiError, getCookieValue(), getCurrentUser(), getGitHubInstallUrl(), getGitHubLoginUrl(), getHealth(), getPullRequestContext(), listGitHubInstallations() (+11 more)

### Community 27 - "Community 27"
Cohesion: 0.29
Nodes (20): FindingCategory, FindingSeverity, _blocking_severities(), build_security_snapshot(), normalize_bandit(), normalize_detect_secrets(), normalize_pip_audit(), _normalize_scanner() (+12 more)

### Community 28 - "Community 28"
Cohesion: 0.26
Nodes (22): allowed_file_paths(), citation_grounding(), decision_lock(), evaluate_review(), forbidden_substrings(), mentioned_file_paths(), must_cite(), no_secrets() (+14 more)

### Community 29 - "Community 29"
Cohesion: 0.16
Nodes (23): deactivate_installation(), _permission_name(), Session, User, remove_installation_repositories(), _remove_missing_installation_repositories(), _remove_stale_user_installation_access(), _remove_stale_user_repository_access() (+15 more)

### Community 30 - "Community 30"
Cohesion: 0.13
Nodes (16): app_core_config, app_models_github_connection, app_models_installation_repository, app_models_quality_gate_config, app_models_repository, app_models_user, app_models_user_repository_access, app_services (+8 more)

### Community 31 - "Community 31"
Cohesion: 0.15
Nodes (19): app_models_oauth_state, cleanup_expired_oauth_states(), consume_oauth_state(), create_oauth_state(), CreatedOAuthState, exchange_code_for_user(), _hash_oauth_value(), Session (+11 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (18): _docker_run_command(), _remove_container(), run_isolated_command(), _runner_resource_limits(), _safe_env(), test_remove_container_swallows_errors(), test_command_result_snapshot_redacts_output(), test_isolated_runner_does_not_pass_app_secrets_to_container() (+10 more)

### Community 33 - "Community 33"
Cohesion: 0.18
Nodes (20): _patch_context(), fake_context(), _post_webhook(), _pull_request_context(), _pull_request_payload(), fixture, _signed_headers(), test_pull_request_webhook_creates_pending_analysis_run() (+12 more)

### Community 34 - "Community 34"
Cohesion: 0.14
Nodes (15): getDashboardSummary(), AlertSeverity, DashboardAlert, DashboardInsight, deriveAlerts(), deriveInsights(), InsightTone, sortRunsByRecency() (+7 more)

### Community 35 - "Community 35"
Cohesion: 0.12
Nodes (16): app_core_errors, app_schemas_repository, decrypt_token(), encrypt_token(), _fernet(), generate_key(), test_token_crypto_round_trip(), test_token_crypto_requires_encryption_key() (+8 more)

### Community 36 - "Community 36"
Cohesion: 0.20
Nodes (19): AST, is_source_file(), analyze_brace_language_file(), analyze_python_file(), build_technical_debt_snapshot(), detect_new_todos(), Path, _python_complexity() (+11 more)

### Community 37 - "Community 37"
Cohesion: 0.10
Nodes (18): CI, First-time setup (developer), Graphify, Graphify Cloud and GitHub PR reviews, Prerequisites, Project layout, Relationship to Quality Gate, AI Review (+10 more)

### Community 38 - "Community 38"
Cohesion: 0.21
Nodes (12): build_ai_review_input(), generate_ai_review_snapshot(), AIReviewError, AIReviewSkipped, BaseModel, build_invocation_config(), Any, test_configure_langsmith_from_settings_copies_env() (+4 more)

### Community 39 - "Community 39"
Cohesion: 0.13
Nodes (15): _archive_url(), _NoAuthOnRedirect, redacted_command(), test_archive_url_uses_api_tarball_endpoint(), test_redirect_drops_authorization_header(), test_redacted_command_masks_token(), email_message, re (+7 more)

### Community 40 - "Community 40"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+10 more)

### Community 41 - "Community 41"
Cohesion: 0.16
Nodes (13): analyzePullRequest(), listPullRequests(), RepositoryPullRequestsPage, EmptyState(), EmptyStateProps, StatusBadge(), StatusBadgeProps, PullRequestTable() (+5 more)

### Community 42 - "Community 42"
Cohesion: 0.16
Nodes (14): executeAnalysisRun(), getRepository(), listAnalysisRuns(), RepositoryAnalysisRunsPage, RepositoryDetailPage, RunTicker(), RunTickerProps, tickClass() (+6 more)

### Community 43 - "Community 43"
Cohesion: 0.20
Nodes (17): execute_analysis_run(), get_analysis_run(), list_analysis_runs(), publish_analysis_run_to_github(), get, post, Session, UUID (+9 more)

### Community 44 - "Community 44"
Cohesion: 0.15
Nodes (8): IsolatedRunnerWorkspace, _make_workspace_writable(), Path, run_command(), test_make_workspace_writable_skips_os_errors(), test_isolated_runner_workspace_paths(), test_run_command_success_and_writable_chmod_continue(), test_run_command_timeout()

### Community 45 - "Community 45"
Cohesion: 0.22
Nodes (14): get_quality_gate_config(), get, put, Session, UUID, update_quality_gate_config(), BaseModel, QualityGateConfigRead (+6 more)

### Community 46 - "Community 46"
Cohesion: 0.16
Nodes (11): repository_clone_url(), _github_archive(), _github_response(), test_command_snapshot_redacts_clone_token(), test_download_repository_archive_extracts_checkout_without_git(), test_github_client_uses_provided_installation_token(), fake_get(), test_pull_request_context_maps_paginated_files_and_truncates_large_diff() (+3 more)

### Community 47 - "Community 47"
Cohesion: 0.16
Nodes (13): logout(), AnalysisDetailPage, App(), AuthenticatedApp(), handleLogout(), DashboardPage, HelpPage, RepositoriesPage (+5 more)

### Community 48 - "Community 48"
Cohesion: 0.30
Nodes (13): build_graph(), compiled_review_graph(), draft(), emit(), load_evidence(), Any, retrieve(), validate() (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.35
Nodes (11): execute_analysis_run(), _expire_analysis_caches(), _finish_with_error(), _get_run_for_execution(), _persist_findings(), Session, UUID, _run_pipeline() (+3 more)

### Community 50 - "Community 50"
Cohesion: 0.25
Nodes (12): getCoverageExecutionConfig(), getQualityGateConfig(), updateCoverageExecutionConfig(), updateQualityGateConfig(), LoadingBlock(), LoadingBlockProps, coveragePreset(), RepositoryQualityGateConfigPage() (+4 more)

### Community 51 - "Community 51"
Cohesion: 0.26
Nodes (10): _correct_draft(), ChangedFileHunkArgs, BaseModel, Any, redact_json_like(), redact_text(), test_redact_json_like_redacts_nested_patch_without_mutating_input(), test_redact_text_masks_github_tokens_private_keys_and_assignments() (+2 more)

### Community 52 - "Community 52"
Cohesion: 0.21
Nodes (10): AIReviewGenerated, _load_example(), test_graph_fail_coverage_passes_decision_lock_and_must_cite(), fake_draft(), test_graph_validation_failure_returns_ai_review_error(), fake_draft(), _fake_analysis_run(), test_generate_ai_review_snapshot_success_and_fallback() (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.18
Nodes (10): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, skipLibCheck, target (+2 more)

### Community 54 - "Community 54"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 55 - "Community 55"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 56 - "Community 56"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 57 - "Community 57"
Cohesion: 0.22
Nodes (8): entrypoint, maxDuration, routePrefix, experimentalServices, backend, frontend, entrypoint, routePrefix

### Community 58 - "Community 58"
Cohesion: 0.29
Nodes (6): CurrentUserRead, BaseModel, GitHubInstallationRead, GitHubInstallUrlRead, BaseModel, pydantic

### Community 59 - "Community 59"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 60 - "Community 60"
Cohesion: 0.47
Nodes (5): _load_examples(), _reference_output(), test_code_evaluators_pass_on_golden_reference_outputs(), test_live_langsmith_eval_optional(), skipif

### Community 61 - "Community 61"
Cohesion: 0.33
Nodes (3): github_writes(), fake_list(), fixture

### Community 63 - "Community 63"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 64 - "Community 64"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 67 - "Community 67"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 68 - "Community 68"
Cohesion: 0.50
Nodes (3): For git commit hook, For native AGENTS.md integration, graphify reference: commit hook and native AGENTS.md integration

### Community 69 - "Community 69"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 72 - "Community 72"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 73 - "Community 73"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 74 - "Community 74"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 75 - "Community 75"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 76 - "Community 76"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 77 - "Community 77"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **222 isolated node(s):** `RunStatusDonutProps`, `AnalysisFinding`, `AnalysisTriggerSource`, `ChangedFileSnapshot`, `CoverageLanguage` (+217 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 578 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture` connect `Community 0` to `Community 1`, `Community 2`, `Community 34`, `Community 9`, `Community 41`, `Community 11`, `Community 12`, `Community 42`, `Community 18`, `Community 26`?**
  _High betweenness centrality (0.208) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `Community 11` to `Community 0`, `Community 1`, `Community 2`, `Community 7`, `Community 9`, `Community 12`, `Community 14`, `Community 19`, `Community 20`, `Community 21`, `Community 29`, `Community 30`, `Community 31`, `Community 32`, `Community 33`, `Community 35`, `Community 38`, `Community 39`, `Community 43`, `Community 44`, `Community 45`, `Community 48`, `Community 49`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `AnalysisRun` connect `Community 1` to `Community 0`, `Community 65`, `Community 2`, `Community 4`, `Community 5`, `Community 38`, `Community 10`, `Community 11`, `Community 13`, `Community 46`, `Community 15`, `Community 49`, `Community 19`, `Community 22`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `AnalysisRun` (e.g. with `AnalysisRunStatus` and `AnalysisTriggerSource`) actually correct?**
  _`AnalysisRun` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `get_settings()` (e.g. with `get_repository()` and `list_pull_requests()`) actually correct?**
  _`get_settings()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 48 inferred relationships involving `AnalysisRunStatus` (e.g. with `AnalysisRun` and `AnalysisRunSummary`) actually correct?**
  _`AnalysisRunStatus` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `AppError` (e.g. with `get_install_url()` and `readiness()`) actually correct?**
  _`AppError` has 19 INFERRED edges - model-reasoned connections that need verification._