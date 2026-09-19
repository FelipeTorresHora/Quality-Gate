import { useEffect, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";

import { executeAnalysisRun } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import LoadingBlock from "../components/LoadingBlock";
import RunTicker from "../components/RunTicker";
import StatusBadge from "../components/StatusBadge";
import type { RepositoryWorkspaceContext } from "./RepositoryDetailPage";

export default function RepositoryAnalysisRunsPage() {
  const { repository, runs, refreshRuns } = useOutletContext<RepositoryWorkspaceContext>();
  const [loading, setLoading] = useState(runs.length === 0);
  const [error, setError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [executingRunId, setExecutingRunId] = useState<string | null>(null);

  useEffect(() => {
    if (runs.length > 0) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    refreshRuns()
      .catch(setError)
      .finally(() => setLoading(false));
  }, [repository.id, refreshRuns, runs.length]);

  async function executeRun(analysisRunId: string) {
    setActionError(null);
    setExecutingRunId(analysisRunId);
    try {
      await executeAnalysisRun(analysisRunId);
      await refreshRuns();
    } catch (caught) {
      setActionError(caught);
    } finally {
      setExecutingRunId(null);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Analysis History</h2>
      </div>
      <ErrorMessage error={error} />
      <ErrorMessage error={actionError} />
      {loading ? (
        <LoadingBlock label="Loading Analysis Runs" />
      ) : runs.length === 0 ? (
        <EmptyState title="No Analysis Runs">
          Analyze a Pull Request from the Pull Requests tab.
        </EmptyState>
      ) : (
        <>
          <div className="run-ticker-inset">
            <RunTicker
              getLabel={(run) => `#${run.pr_number} · ${run.decision ?? run.status}`}
              runs={runs}
            />
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>PR</th>
                  <th>Status</th>
                  <th>Decision</th>
                  <th>Score</th>
                  <th>Trigger</th>
                  <th>Head SHA</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id}>
                    <td>#{run.pr_number}</td>
                    <td>
                      <StatusBadge value={run.status} />
                    </td>
                    <td>
                      <StatusBadge value={run.decision} />
                    </td>
                    <td className="mono-value">{run.score ?? "-"}</td>
                    <td>
                      <StatusBadge value={run.trigger_source} />
                    </td>
                    <td>
                      <code className="mono-value">{shortSha(run.head_sha)}</code>
                    </td>
                    <td className="mono-value">{new Date(run.created_at).toLocaleString()}</td>
                    <td>
                      <div className="badge-row">
                        {run.status === "pending" && (
                          <button
                            className="button small primary"
                            disabled={executingRunId === run.id}
                            onClick={() => executeRun(run.id)}
                            type="button"
                          >
                            {executingRunId === run.id ? "Executing" : "Execute"}
                          </button>
                        )}
                        <Link to={`/analysis-runs/${run.id}`}>Detail</Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

function shortSha(value: string) {
  return value.length > 12 ? value.slice(0, 12) : value;
}
