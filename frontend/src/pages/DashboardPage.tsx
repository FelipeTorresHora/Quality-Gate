import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getDashboardSummary } from "../api/client";
import AlertsPanel from "../components/AlertsPanel";
import FindingsBar from "../components/charts/FindingsBar";
import RunStatusDonut from "../components/charts/RunStatusDonut";
import ScoreSparkline from "../components/charts/ScoreSparkline";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import InsightCards from "../components/InsightCards";
import LoadingBlock from "../components/LoadingBlock";
import RunTicker from "../components/RunTicker";
import StatusBadge from "../components/StatusBadge";
import { deriveAlerts, deriveInsights } from "../lib/insights";
import type { DashboardSummary } from "../types/api";

const runStatuses = ["pending", "running", "completed", "error"] as const;
const gateDecisions = ["pass", "fail"] as const;

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    getDashboardSummary().then(setSummary).catch(setError);
  }, []);

  if (error) {
    return (
      <div className="page-stack">
        <ErrorMessage error={error} />
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="page-stack">
        <LoadingBlock label="Loading dashboard summary" />
      </div>
    );
  }

  const alerts = deriveAlerts(summary);
  const insights = deriveInsights(summary);

  return (
    <div className="page-stack animate-in">
      <header className="page-header">
        <div>
          <p className="eyebrow">Operations</p>
          <h1>Quality Gate Dashboard</h1>
        </div>
        <Link className="button primary" to="/repositories">
          Repositories
        </Link>
      </header>

      {summary.total_repositories === 0 && (
        <EmptyState
          action={
            <Link className="button primary" to="/repositories">
              Manage GitHub App
            </Link>
          }
          title="No repositories registered"
        >
          Install the GitHub App to start analyzing Pull Requests.
        </EmptyState>
      )}

      <RunTicker
        getLabel={(run) => {
          const withRepo = summary.recent_analysis_runs.find((r) => r.id === run.id);
          const decision = run.decision ?? run.status;
          return `${withRepo?.repository_full_name ?? "repo"} #${run.pr_number} · ${decision}`;
        }}
        runs={summary.recent_analysis_runs}
      />

      <AlertsPanel alerts={alerts} />

      <InsightCards insights={insights} />

      <section className="metrics-grid four">
        <div className="metric">
          <span>Repositories</span>
          <strong>{summary.total_repositories}</strong>
        </div>
        <div className="metric">
          <span>Analysis Runs</span>
          <strong>{summary.total_analysis_runs}</strong>
        </div>
        <div className="metric">
          <span>Approval Rate</span>
          <strong>
            {summary.approval_rate === null ? "-" : `${summary.approval_rate}%`}
          </strong>
        </div>
        <div className="metric highlight">
          <span>Blocking Categories</span>
          <strong>{summary.top_blocking_categories.length}</strong>
        </div>
      </section>

      <section className="split-layout even">
        <div className="panel">
          <div className="panel-header">
            <h2>Run Status</h2>
          </div>
          <RunStatusDonut counts={summary.run_status_counts} />
          <div className="compact-list">
            {runStatuses.map((status) => (
              <div className="compact-row" key={status}>
                <StatusBadge value={status} />
                <strong>{summary.run_status_counts[status]}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Findings by Category</h2>
          </div>
          {summary.finding_counts.length === 0 ? (
            <EmptyState title="No Analysis Findings">
              Findings will appear after Pull Request analyses.
            </EmptyState>
          ) : (
            <FindingsBar findingCounts={summary.finding_counts} />
          )}
        </div>
      </section>

      {summary.recent_analysis_runs.length > 0 && (
        <section className="panel">
          <div className="panel-header">
            <h2>Score Trend</h2>
            <p className="panel-subtitle">Recent completed runs, chronological</p>
          </div>
          <ScoreSparkline runs={summary.recent_analysis_runs} />
        </section>
      )}

      <section className="split-layout">
        <div className="panel">
          <div className="panel-header">
            <h2>Recent Analysis Runs</h2>
          </div>
          {summary.recent_analysis_runs.length === 0 ? (
            <EmptyState title="No Analysis Runs">
              Analyze a Pull Request from a repository workspace.
            </EmptyState>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Repository</th>
                    <th>PR</th>
                    <th>Status</th>
                    <th>Decision</th>
                    <th>Score</th>
                    <th>Trigger</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.recent_analysis_runs.map((run) => (
                    <tr key={run.id}>
                      <td>
                        <Link to={`/repositories/${run.repository_id}`}>
                          {run.repository_full_name}
                        </Link>
                      </td>
                      <td>
                        <Link to={`/analysis-runs/${run.id}`}>#{run.pr_number}</Link>
                      </td>
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
                      <td className="mono-value">{new Date(run.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Top Blocking Categories</h2>
          </div>
          {summary.top_blocking_categories.length === 0 ? (
            <EmptyState title="No blocking findings">
              Blocking categories will appear when findings block a gate.
            </EmptyState>
          ) : (
            <div className="compact-list">
              {summary.top_blocking_categories.map((item) => (
                <div className="compact-row" key={item.category}>
                  <StatusBadge value={item.category} />
                  <strong>{item.count}</strong>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
