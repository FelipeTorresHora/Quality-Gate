import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useOutletContext } from "react-router-dom";

import {
  createMockAnalysisRun,
  executeAnalysisRun,
  listPullRequests
} from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import LoadingBlock from "../components/LoadingBlock";
import StatusBadge from "../components/StatusBadge";
import type { RepositoryWorkspaceContext } from "./RepositoryDetailPage";
import type { GitHubPullRequest, MockScenario } from "../types/api";

const scenarios: MockScenario[] = [
  "passing",
  "coverage_fail",
  "security_fail",
  "technical_debt_fail",
  "mixed_fail"
];

export default function RepositoryPullRequestsPage() {
  const { repository } = useOutletContext<RepositoryWorkspaceContext>();
  const navigate = useNavigate();
  const [pullRequests, setPullRequests] = useState<GitHubPullRequest[]>([]);
  const [selectedScenario, setSelectedScenario] =
    useState<MockScenario>("mixed_fail");
  const [manualPrNumber, setManualPrNumber] = useState(1);
  const [manualHeadSha, setManualHeadSha] = useState("mock-head-sha");
  const [loading, setLoading] = useState(repository.github_repo_id !== null);
  const [error, setError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [executingRunId, setExecutingRunId] = useState<string | null>(null);

  useEffect(() => {
    if (repository.github_repo_id === null) {
      setPullRequests([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    listPullRequests(repository.id)
      .then(setPullRequests)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [repository.id, repository.github_repo_id]);

  async function createScenario(prNumber: number, headSha: string) {
    setActionError(null);
    try {
      const run = await createMockAnalysisRun(repository.id, {
        scenario: selectedScenario,
        pr_number: prNumber,
        head_sha: headSha
      });
      navigate(`/analysis-runs/${run.id}`);
    } catch (caught) {
      setActionError(caught);
    }
  }

  async function executeRun(analysisRunId: string) {
    setActionError(null);
    setExecutingRunId(analysisRunId);
    try {
      const run = await executeAnalysisRun(analysisRunId);
      navigate(`/analysis-runs/${run.id}`);
    } catch (caught) {
      setActionError(caught);
    } finally {
      setExecutingRunId(null);
    }
  }

  function handleManualSubmit(event: FormEvent) {
    event.preventDefault();
    createScenario(manualPrNumber, manualHeadSha);
  }

  return (
    <div className="page-stack">
      <ErrorMessage error={actionError} />

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Mock Analysis Controls</h2>
            <p className="panel-subtitle">
              Create mock-only Analysis Runs for dashboard validation.
            </p>
          </div>
        </div>
        <form className="form-grid" onSubmit={handleManualSubmit}>
          <label>
            Scenario
            <select
              value={selectedScenario}
              onChange={(event) =>
                setSelectedScenario(event.target.value as MockScenario)
              }
            >
              {scenarios.map((scenario) => (
                <option key={scenario} value={scenario}>
                  {scenario}
                </option>
              ))}
            </select>
          </label>
          <label>
            PR number
            <input
              min="1"
              type="number"
              value={manualPrNumber}
              onChange={(event) => setManualPrNumber(Number(event.target.value))}
            />
          </label>
          <label>
            Head SHA
            <input
              value={manualHeadSha}
              onChange={(event) => setManualHeadSha(event.target.value)}
            />
          </label>
          <button className="button primary" type="submit">
            Create Mock Analysis
          </button>
        </form>
      </section>

      {repository.github_repo_id === null ? (
        <EmptyState title="Manual repository">
          GitHub Pull Requests are not available for manual repositories.
        </EmptyState>
      ) : (
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Pull Request Review Queue</h2>
              <p className="panel-subtitle">
                Latest backend review state is matched against the live PR head SHA.
              </p>
            </div>
          </div>
          <ErrorMessage error={error} />
          {loading ? (
            <LoadingBlock label="Loading Pull Requests" />
          ) : (
            <PullRequestTable
              executingRunId={executingRunId}
              onCreateMockAnalysis={createScenario}
              onExecuteAnalysis={executeRun}
              pullRequests={pullRequests}
            />
          )}
        </section>
      )}
    </div>
  );
}

function PullRequestTable({
  executingRunId,
  onCreateMockAnalysis,
  onExecuteAnalysis,
  pullRequests
}: {
  executingRunId: string | null;
  onCreateMockAnalysis: (prNumber: number, headSha: string) => void;
  onExecuteAnalysis: (analysisRunId: string) => void;
  pullRequests: GitHubPullRequest[];
}) {
  if (pullRequests.length === 0) {
    return (
      <EmptyState title="No open Pull Requests">
        Open Pull Requests from GitHub will appear here.
      </EmptyState>
    );
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>PR</th>
            <th>Title</th>
            <th>Author</th>
            <th>State</th>
            <th>Branches</th>
            <th>Head SHA</th>
            <th>Review State</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {pullRequests.map((pullRequest) => (
            <tr key={pullRequest.number}>
              <td>#{pullRequest.number}</td>
              <td>
                <a href={pullRequest.html_url} rel="noreferrer" target="_blank">
                  {pullRequest.title}
                </a>
              </td>
              <td>{pullRequest.user_login}</td>
              <td>
                <div className="badge-row">
                  <StatusBadge value={pullRequest.draft ? "draft" : pullRequest.state} />
                </div>
              </td>
              <td>
                {pullRequest.head_ref} to {pullRequest.base_ref}
              </td>
              <td>
                <code className="mono-value">{shortSha(pullRequest.head_sha)}</code>
              </td>
              <td>
                <ReviewStateCell pullRequest={pullRequest} />
              </td>
              <td>
                <PullRequestActions
                  executingRunId={executingRunId}
                  onCreateMockAnalysis={onCreateMockAnalysis}
                  onExecuteAnalysis={onExecuteAnalysis}
                  pullRequest={pullRequest}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PullRequestActions({
  executingRunId,
  onCreateMockAnalysis,
  onExecuteAnalysis,
  pullRequest
}: {
  executingRunId: string | null;
  onCreateMockAnalysis: (prNumber: number, headSha: string) => void;
  onExecuteAnalysis: (analysisRunId: string) => void;
  pullRequest: GitHubPullRequest;
}) {
  const run = pullRequest.review_state.analysis_run;
  const canExecute =
    pullRequest.review_state.state === "current" && run?.status === "pending";

  if (canExecute && run) {
    return (
      <button
        className="button small primary"
        disabled={executingRunId === run.id}
        onClick={() => onExecuteAnalysis(run.id)}
        type="button"
      >
        {executingRunId === run.id ? "Executing" : "Execute Analysis"}
      </button>
    );
  }

  return (
    <button
      className="button small secondary"
      onClick={() =>
        onCreateMockAnalysis(
          pullRequest.number,
          pullRequest.head_sha
        )
      }
      type="button"
    >
      Create Mock Analysis
    </button>
  );
}

function ReviewStateCell({ pullRequest }: { pullRequest: GitHubPullRequest }) {
  const review = pullRequest.review_state;
  const run = review.analysis_run;

  if (!run) {
    return <StatusBadge value="not_run" />;
  }

  if (review.state === "outdated") {
    return (
      <div className="stacked-cell">
        <StatusBadge value="outdated" />
        <span>New commits</span>
        <Link to={`/analysis-runs/${run.id}`}>Previous run</Link>
      </div>
    );
  }

  return (
    <div className="stacked-cell">
      <div className="badge-row">
        <StatusBadge value={run.status} />
        <StatusBadge value={run.decision} />
      </div>
      <span>Score {run.score ?? "-"}</span>
      <Link to={`/analysis-runs/${run.id}`}>View detail</Link>
    </div>
  );
}

function shortSha(value: string) {
  return value.length > 12 ? value.slice(0, 12) : value;
}
