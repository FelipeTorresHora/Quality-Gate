import { lazy, Suspense, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getDashboardSummary } from "../api/client";
import AlertsPanel from "../components/AlertsPanel";
const FindingsBar = lazy(() => import("../components/charts/FindingsBar"));
const RunStatusDonut = lazy(() => import("../components/charts/RunStatusDonut"));
const ScoreSparkline = lazy(() => import("../components/charts/ScoreSparkline"));
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import InsightCards from "../components/InsightCards";
import LoadingBlock from "../components/LoadingBlock";
import RunTicker from "../components/RunTicker";
import StatusBadge from "../components/StatusBadge";
import { deriveAlerts, deriveInsights } from "../lib/insights";
import type { DashboardOpenPullRequestAction, DashboardSummary } from "../types/api";

const runStatuses = ["pending", "running", "completed", "error"] as const;
function ChartPlaceholder({ small = false }: { small?: boolean }) {
  return (
    <div
      aria-hidden="true"
      className={small ? "chart-panel small chart-panel-loading" : "chart-panel chart-panel-loading"}
    />
  );
}

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

      {summary.total_repositories > 0 && (
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Open Pull Requests needing action</h2>
              <p className="panel-subtitle">
                Fail, operational error, outdated analysis, or GitHub publication
                turned off. Passing current reviews stay off this queue.
              </p>
            </div>
          </div>
          {summary.open_pull_requests_needing_action.length === 0 ? (
            <EmptyState title="No open Pull Requests need action">
              Open Pull Requests that failed the quality gate, hit an operational
              error, or have an outdated analysis will appear here.
            </EmptyState>
          ) : (
            <OpenPullRequestActionTable
              items={summary.open_pull_requests_needing_action}
            />
          )}
        </section>
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

      <section className="split-layout even dashboard-below-fold">
        <div className="panel">
          <div className="panel-header">
            <h2>Run Status</h2>
          </div>
          <Suspense fallback={<ChartPlaceholder />}>
            <RunStatusDonut counts={summary.run_status_counts} />
          </Suspense>
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
            <Suspense fallback={<ChartPlaceholder />}>
              <FindingsBar findingCounts={summary.finding_counts} />
            </Suspense>
          )}
        </div>
      </section>

      {summary.recent_analysis_runs.length > 0 && (
        <section className="panel dashboard-below-fold">
          <div className="panel-header">
            <h2>Score Trend</h2>
            <p className="panel-subtitle">Recent completed runs, chronological</p>
          </div>
          <Suspense fallback={<ChartPlaceholder small />}>
            <ScoreSparkline runs={summary.recent_analysis_runs} />
          </Suspense>
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

const actionCopy: Record<DashboardOpenPullRequestAction["action"], string> = {
  fail: "fail",
  error: "error",
  outdated: "outdated",
  publication_off: "publication_off"
};

function OpenPullRequestActionTable({
  items
}: {
  items: DashboardOpenPullRequestAction[];
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Repository</th>
            <th>PR</th>
            <th>SHA</th>
            <th>Status</th>
            <th>Decision</th>
            <th>Review</th>
            <th>Action</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={`${item.repository_id}-${item.pr_number}`}>
              <td>
                <Link to={`/repositories/${item.repository_id}`}>
                  {item.repository_full_name}
                </Link>
              </td>
              <td>
                <div className="stacked-cell">
                  <Link to={`/analysis-runs/${item.analysis_run_id}`}>
                    #{item.pr_number}
                  </Link>
                  {item.pr_title ? <span>{item.pr_title}</span> : null}
                </div>
              </td>
              <td>
                <code className="mono-value">{shortSha(item.head_sha)}</code>
              </td>
              <td>
                <StatusBadge value={item.status} />
              </td>
              <td>
                <StatusBadge value={item.decision} />
              </td>
              <td>
                <StatusBadge value={item.review_state} />
              </td>
              <td>
                <StatusBadge value={actionCopy[item.action]} />
              </td>
              <td>
                <div className="badge-row">
                  <Link to={`/analysis-runs/${item.analysis_run_id}`}>View run</Link>
                  {item.html_url ? (
                    <a href={item.html_url} rel="noreferrer" target="_blank">
                      GitHub
                    </a>
                  ) : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function shortSha(value: string) {
  return value.length > 12 ? value.slice(0, 12) : value;
}
