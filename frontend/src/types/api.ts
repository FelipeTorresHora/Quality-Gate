export type CurrentUser = {
  id: string;
  github_user_id: number;
  github_login: string;
  name: string | null;
  avatar_url: string | null;
  has_github_connection: boolean;
};

export type GitHubInstallation = {
  installation_id: number;
  account_login: string;
  account_type: string;
  active: boolean;
};

export type GitHubInstallUrl = {
  url: string;
};

export type Repository = {
  id: string;
  github_repo_id: number | null;
  owner: string;
  name: string;
  full_name: string;
  default_branch: string;
  created_at: string;
  updated_at: string;
};

export type FindingCategory =
  | "coverage"
  | "security"
  | "technical_debt"
  | "code_review";

export type FindingSeverity = "low" | "medium" | "high" | "critical";

export type FindingSource = "deterministic" | "ai";

export type GateEvaluationMode = "hybrid" | "deterministic" | "ai_only";

export type AlertDisposition = "confirm" | "downgrade" | "dismiss";

export type SecurityScanner = "semgrep" | "detect-secrets" | "bandit" | "pip-audit";

export type QualityGateConfig = {
  id: string;
  repository_id: string;
  min_total_coverage: number;
  max_coverage_drop: number;
  min_changed_files_coverage: number;
  coverage_enabled: boolean;
  security_fail_on: string[] | Record<string, unknown>;
  security_enabled: boolean;
  max_function_lines: number;
  max_complexity: number;
  fail_on_new_todo: boolean;
  technical_debt_enabled: boolean;
  code_review_enabled: boolean;
  coverage_mode: GateEvaluationMode;
  security_mode: GateEvaluationMode;
  technical_debt_mode: GateEvaluationMode;
  comment_on_github: boolean;
  publish_github_status: boolean;
  created_at: string;
  updated_at: string;
};

export type AnalysisFinding = {
  id: string;
  analysis_run_id: string;
  category: FindingCategory;
  severity: FindingSeverity;
  file_path: string | null;
  line_number: number | null;
  title: string;
  description: string;
  blocking: boolean;
  source: FindingSource;
  confidence: number | null;
  suggestion_code: string | null;
  created_at: string;
};

export type AnalysisTriggerSource = "manual" | "github_webhook";

export type PullRequestSnapshot = {
  number: number;
  title: string;
  body: string | null;
  state: string;
  draft: boolean;
  author_login: string;
  html_url: string;
  base_ref: string;
  head_ref: string;
  head_sha: string;
  base_sha: string | null;
  created_at: string;
  updated_at: string;
};

export type ChangedFileSnapshot = {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  changes: number;
  patch: string | null;
};

export type PullRequestContext = {
  pull_request: PullRequestSnapshot;
  changed_files: ChangedFileSnapshot[];
  diff_snapshot: string;
  diff_truncated: boolean;
};

export type AnalysisRunSummary = {
  id: string;
  repository_id: string;
  pr_number: number;
  head_sha: string;
  status: "pending" | "running" | "completed" | "error";
  decision: "pass" | "fail" | null;
  trigger_source: AnalysisTriggerSource;
  score: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type InlineComment = {
  file_path: string;
  line_number: number;
  title: string;
  body: string;
  severity: FindingSeverity;
  confidence: number;
  suggestion_code: string | null;
  category: "code_review";
};

export type AIGateFinding = {
  category: FindingCategory;
  severity: FindingSeverity;
  file_path: string | null;
  line_number: number | null;
  title: string;
  description: string;
  confidence: number;
  suggestion_code: string | null;
  source: "ai";
  blocking: false;
};

export type TriagedAlert = {
  scanner: SecurityScanner;
  rule_id: string | null;
  file_path: string | null;
  line_number: number | null;
  severity: FindingSeverity;
  title: string;
  description: string;
  confidence: number;
  disposition: AlertDisposition;
  rationale: string;
  suggestion_code: string | null;
};

export type AICoverageReview = {
  summary: string;
  coverage_assessment: string;
  findings: AIGateFinding[];
};

export type AISecurityReview = {
  summary: string;
  security_assessment: string;
  triaged_alerts: TriagedAlert[];
  findings: AIGateFinding[];
};

export type AITechDebtReview = {
  summary: string;
  technical_debt_assessment: string;
  findings: AIGateFinding[];
};

export type PillarInsights = {
  coverage: AICoverageReview | null;
  security: AISecurityReview | null;
  technical_debt: AITechDebtReview | null;
};

export type ContextBudgetMetadata = {
  batches_sent: number;
  batches_total: number;
  review_truncated: boolean;
  skipped_files: string[];
  batch_max_chars: number | null;
  max_batches: number | null;
  pillar_max_chars: number | null;
};

export type AIReviewSnapshot =
  | {
      status: "generated";
      model: string;
      generated_at: string;
      score: number;
      summary: string;
      risk_level: "low" | "medium" | "high";
      blocking_reasons: string[];
      suggestions: string[];
      coverage_assessment: string;
      security_assessment: string;
      technical_debt_assessment: string;
      inline_comments?: InlineComment[];
      pillar_insights?: PillarInsights;
      context_budget?: ContextBudgetMetadata;
    }
  | {
      status: "partial";
      model: string;
      generated_at: string;
      score: number | null;
      summary: string;
      risk_level: "low" | "medium" | "high";
      blocking_reasons: string[];
      suggestions: string[];
      coverage_assessment: string;
      security_assessment: string;
      technical_debt_assessment: string;
      inline_comments: InlineComment[];
      pillar_insights: PillarInsights;
      context_budget: ContextBudgetMetadata;
      reason: "context_budget_exhausted";
    }
  | {
      status: "skipped";
      reason: "openai_api_key_missing";
    }
  | {
      status: "error";
      reason: "ai_review_failed";
      message: string;
    }
  | Record<string, never>;

export type CoverageLanguage = "python" | "typescript" | "javascript" | "go";

export type CoverageReportFormat = "cobertura_xml" | "lcov" | "go_coverprofile";

export type CoverageExecutionConfig = {
  id: string;
  repository_id: string;
  language: CoverageLanguage;
  language_preset_confirmed: boolean;
  install_command: string;
  working_directory: string;
  test_command: string;
  report_path: string;
  report_format: CoverageReportFormat;
  created_at: string;
  updated_at: string;
};

export type DashboardRecentAnalysisRun = AnalysisRunSummary & {
  repository_full_name: string;
};

export type DashboardFindingCount = {
  category: FindingCategory;
  severity: FindingSeverity;
  count: number;
};

export type DashboardBlockingCategory = {
  category: FindingCategory;
  count: number;
};

export type DashboardOpenPullRequestAction = {
  repository_id: string;
  repository_full_name: string;
  pr_number: number;
  pr_title: string | null;
  html_url: string | null;
  head_sha: string;
  analysis_run_id: string;
  status: AnalysisRunSummary["status"];
  decision: AnalysisRunSummary["decision"];
  review_state: PullRequestReviewState["state"];
  action: "fail" | "error" | "outdated" | "publication_off";
  comment_on_github: boolean;
  publish_github_status: boolean;
  created_at: string;
};

export type DashboardSummary = {
  total_repositories: number;
  total_analysis_runs: number;
  run_status_counts: Record<AnalysisRunSummary["status"], number>;
  gate_decision_counts: Record<NonNullable<AnalysisRunSummary["decision"]>, number>;
  approval_rate: number | null;
  recent_analysis_runs: DashboardRecentAnalysisRun[];
  finding_counts: DashboardFindingCount[];
  top_blocking_categories: DashboardBlockingCategory[];
  open_pull_requests_needing_action: DashboardOpenPullRequestAction[];
};

export type AnalysisRunDetail = AnalysisRunSummary & {
  coverage_result_json: Record<string, unknown>;
  security_result_json: Record<string, unknown>;
  technical_debt_result_json: Record<string, unknown>;
  ai_review_json: AIReviewSnapshot;
  pull_request_snapshot_json: Partial<PullRequestSnapshot>;
  changed_files_snapshot_json: ChangedFileSnapshot[];
  diff_truncated: boolean;
  final_report_markdown: string | null;
  findings: AnalysisFinding[];
};

export type GitHubPublicationResult = {
  analysis_run_id: string;
  comment: {
    enabled: boolean;
    published: boolean;
    html_url: string | null;
    skipped_reason: string | null;
  };
    commit_status: {
    enabled: boolean;
    published: boolean;
    target_sha: string | null;
    state: string | null;
    target_url: string | null;
    skipped_reason: string | null;
  };
};

export type PullRequestReviewRun = {
  id: string;
  status: AnalysisRunSummary["status"];
  decision: AnalysisRunSummary["decision"];
  score: number | null;
  trigger_source: AnalysisTriggerSource;
  head_sha: string;
  created_at: string;
};

export type PullRequestReviewState = {
  state: "not_run" | "current" | "outdated";
  analysis_run: PullRequestReviewRun | null;
};

export type GitHubPullRequest = {
  number: number;
  title: string;
  user_login: string;
  state: string;
  draft: boolean;
  head_ref: string;
  head_sha: string;
  base_ref: string;
  html_url: string;
  created_at: string;
  updated_at: string;
  review_state: PullRequestReviewState;
};

export type ApiErrorDetail = {
  code: string;
  message: string;
};
