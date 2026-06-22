import type {
  AnalysisRunDetail,
  AnalysisRunSummary,
  ApiErrorDetail,
  CoverageExecutionConfig,
  DashboardSummary,
  GitHubPullRequest,
  MockScenario,
  PullRequestContext,
  QualityGateConfig,
  Repository
} from "../types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export class ApiError extends Error {
  detail: ApiErrorDetail;
  status: number;

  constructor(status: number, detail: ApiErrorDetail) {
    super(detail.message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {})
    }
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail ?? {
      code: "request_failed",
      message: "Request failed."
    };
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export function getHealth() {
  return request<{ status: string }>("/health");
}

export function getDashboardSummary() {
  return request<DashboardSummary>("/api/dashboard/summary");
}

export function listRepositories() {
  return request<Repository[]>("/api/repositories");
}

export function createRepository(payload: {
  owner: string;
  name: string;
  full_name?: string;
  default_branch: string;
}) {
  return request<Repository>("/api/repositories", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function createGitHubRepository(payload: { owner: string; name: string }) {
  return request<Repository>("/api/repositories/github", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getRepository(repositoryId: string) {
  return request<Repository>(`/api/repositories/${repositoryId}`);
}

export function listPullRequests(repositoryId: string) {
  return request<GitHubPullRequest[]>(
    `/api/repositories/${repositoryId}/pull-requests`
  );
}

export function getPullRequestContext(repositoryId: string, prNumber: number) {
  return request<PullRequestContext>(
    `/api/repositories/${repositoryId}/pull-requests/${prNumber}/context`
  );
}

export function getQualityGateConfig(repositoryId: string) {
  return request<QualityGateConfig>(
    `/api/repositories/${repositoryId}/quality-gate-config`
  );
}

export function getCoverageExecutionConfig(repositoryId: string) {
  return request<CoverageExecutionConfig>(
    `/api/repositories/${repositoryId}/coverage-execution-config`
  );
}

export function updateCoverageExecutionConfig(
  repositoryId: string,
  payload: Partial<CoverageExecutionConfig>
) {
  return request<CoverageExecutionConfig>(
    `/api/repositories/${repositoryId}/coverage-execution-config`,
    {
      method: "PUT",
      body: JSON.stringify(payload)
    }
  );
}

export function updateQualityGateConfig(
  repositoryId: string,
  payload: Partial<QualityGateConfig>
) {
  return request<QualityGateConfig>(
    `/api/repositories/${repositoryId}/quality-gate-config`,
    {
      method: "PUT",
      body: JSON.stringify(payload)
    }
  );
}

export function listAnalysisRuns(repositoryId: string) {
  return request<AnalysisRunSummary[]>(
    `/api/repositories/${repositoryId}/analysis-runs`
  );
}

export function createMockAnalysisRun(
  repositoryId: string,
  payload: { scenario: MockScenario; pr_number: number; head_sha: string }
) {
  return request<AnalysisRunDetail>(
    `/api/repositories/${repositoryId}/analysis-runs/mock`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function getAnalysisRun(analysisRunId: string) {
  return request<AnalysisRunDetail>(`/api/analysis-runs/${analysisRunId}`);
}

export function executeAnalysisRun(analysisRunId: string) {
  return request<AnalysisRunDetail>(`/api/analysis-runs/${analysisRunId}/execute`, {
    method: "POST"
  });
}
