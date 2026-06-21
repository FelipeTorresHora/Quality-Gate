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

export type QualityGateConfig = {
  id: string;
  repository_id: string;
  min_total_coverage: number;
  max_coverage_drop: number;
  min_changed_files_coverage: number;
  security_fail_on: string[] | Record<string, unknown>;
  max_function_lines: number;
  max_complexity: number;
  fail_on_new_todo: boolean;
  comment_on_github: boolean;
  publish_github_status: boolean;
  created_at: string;
  updated_at: string;
};

export type AnalysisFinding = {
  id: string;
  analysis_run_id: string;
  category: "coverage" | "security" | "technical_debt";
  severity: "low" | "medium" | "high" | "critical";
  file_path: string | null;
  line_number: number | null;
  title: string;
  description: string;
  blocking: boolean;
  created_at: string;
};

export type AnalysisTriggerSource = "mock" | "manual" | "github_webhook";

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

export type AnalysisRunDetail = AnalysisRunSummary & {
  coverage_result_json: Record<string, unknown>;
  security_result_json: Record<string, unknown>;
  technical_debt_result_json: Record<string, unknown>;
  pull_request_snapshot_json: Partial<PullRequestSnapshot>;
  changed_files_snapshot_json: ChangedFileSnapshot[];
  diff_truncated: boolean;
  final_report_markdown: string | null;
  findings: AnalysisFinding[];
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
};

export type MockScenario =
  | "passing"
  | "coverage_fail"
  | "security_fail"
  | "technical_debt_fail"
  | "mixed_fail";

export type ApiErrorDetail = {
  code: string;
  message: string;
};
