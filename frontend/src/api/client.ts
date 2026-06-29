import type {
  AnalysisRunDetail,
  AnalysisRunSummary,
  ApiErrorDetail,
  CoverageExecutionConfig,
  CurrentUser,
  DashboardSummary,
  GitHubInstallation,
  GitHubInstallUrl,
  GitHubPublicationResult,
  GitHubPullRequest,
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
    credentials: "include",
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

export function getGitHubLoginUrl() {
  return `${API_BASE_URL}/api/auth/github/login`;
}

export function getCurrentUser() {
  return request<CurrentUser>("/api/auth/me");
}

export function logout() {
  return request<{ status: string }>("/api/auth/logout", { method: "POST" });
}

export function listGitHubInstallations() {
  return request<GitHubInstallation[]>("/api/github/installations");
}

export function getGitHubInstallUrl() {
  return request<GitHubInstallUrl>("/api/github/installations/install-url");
}

export function getDashboardSummary() {
  return request<DashboardSummary>("/api/dashboard/summary");
}

export function listRepositories() {
  return request<Repository[]>("/api/repositories");
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

export function analyzePullRequest(repositoryId: string, prNumber: number) {
  return request<AnalysisRunDetail>(
    `/api/repositories/${repositoryId}/pull-requests/${prNumber}/analyze`,
    { method: "POST" }
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

export function getAnalysisRun(analysisRunId: string) {
  return request<AnalysisRunDetail>(`/api/analysis-runs/${analysisRunId}`);
}

export function executeAnalysisRun(analysisRunId: string) {
  return request<AnalysisRunDetail>(`/api/analysis-runs/${analysisRunId}/execute`, {
    method: "POST"
  });
}

export function publishAnalysisRunToGitHub(analysisRunId: string) {
  return request<GitHubPublicationResult>(
    `/api/analysis-runs/${analysisRunId}/publish-github`,
    {
      method: "POST"
    }
  );
}
