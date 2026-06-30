import { useEffect, useState } from "react";
import { Link, useNavigate, useOutletContext } from "react-router-dom";

import { analyzePullRequest, listPullRequests } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import LoadingBlock from "../components/LoadingBlock";
import StatusBadge from "../components/StatusBadge";
import type { GitHubPullRequest } from "../types/api";
import type { RepositoryWorkspaceContext } from "./RepositoryDetailPage";

export default function RepositoryPullRequestsPage() {
  const { repository } = useOutletContext<RepositoryWorkspaceContext>();
  const navigate = useNavigate();
  const [pullRequests, setPullRequests] = useState<GitHubPullRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [analyzingPrNumber, setAnalyzingPrNumber] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listPullRequests(repository.id)
      .then(setPullRequests)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [repository.id]);

  async function analyze(prNumber: number) {
    setActionError(null);
    setAnalyzingPrNumber(prNumber);
    try {
      const run = await analyzePullRequest(repository.id, prNumber);
      navigate(`/analysis-runs/${run.id}`);
    } catch (caught) {
      setActionError(caught);
      setAnalyzingPrNumber(null);
    }
  }

  return (
    <div className="page-stack">
      <ErrorMessage error={actionError} />
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Pull Request Review Queue</h2>
            <p className="panel-subtitle">
              Review state is matched against each live Pull Request head SHA.
            </p>
          </div>
        </div>
        <ErrorMessage error={error} />
        {loading ? (
          <LoadingBlock label="Loading Pull Requests" />
        ) : (
          <PullRequestTable
            analyzingPrNumber={analyzingPrNumber}
            onAnalyze={analyze}
            pullRequests={pullRequests}
          />
        )}
      </section>
    </div>
  );
}

function PullRequestTable({
  analyzingPrNumber,
  onAnalyze,
  pullRequests
}: {
  analyzingPrNumber: number | null;
  onAnalyze: (prNumber: number) => void;
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
                  analyzing={analyzingPrNumber === pullRequest.number}
                  onAnalyze={onAnalyze}
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
  analyzing,
  onAnalyze,
  pullRequest
}: {
  analyzing: boolean;
  onAnalyze: (prNumber: number) => void;
  pullRequest: GitHubPullRequest;
}) {
  const run = pullRequest.review_state.analysis_run;
  if (!run || pullRequest.review_state.state === "outdated" || run.status === "error") {
    return (
      <button
        className="button small primary"
        disabled={analyzing}
        onClick={() => onAnalyze(pullRequest.number)}
        type="button"
      >
        {analyzing ? "Analyzing" : "Analyze"}
      </button>
    );
  }
  return <Link to={`/analysis-runs/${run.id}`}>View detail</Link>;
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
