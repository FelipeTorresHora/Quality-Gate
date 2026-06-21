import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getAnalysisRun } from "../api/client";
import ErrorMessage from "../components/ErrorMessage";
import StatusBadge from "../components/StatusBadge";
import type { AnalysisRunDetail, PullRequestSnapshot } from "../types/api";

export default function AnalysisDetailPage() {
  const { analysisRunId } = useParams();
  const [run, setRun] = useState<AnalysisRunDetail | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    if (!analysisRunId) {
      return;
    }
    getAnalysisRun(analysisRunId).then(setRun).catch(setError);
  }, [analysisRunId]);

  if (!run) {
    return (
      <div className="page-stack">
        <ErrorMessage error={error} />
      </div>
    );
  }

  const pullRequestContext = hasPullRequestSnapshot(run.pull_request_snapshot_json)
    ? run.pull_request_snapshot_json
    : null;

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Analysis Run</p>
          <h1>PR #{run.pr_number}</h1>
        </div>
        <Link className="button" to={`/repositories/${run.repository_id}`}>
          Repository
        </Link>
      </header>

      <section className="metrics-grid six">
        <div className="metric">
          <span>Status</span>
          <strong>
            <StatusBadge value={run.status} />
          </strong>
        </div>
        <div className="metric">
          <span>Decision</span>
          <strong>
            <StatusBadge value={run.decision} />
          </strong>
        </div>
        <div className="metric">
          <span>Score</span>
          <strong>{run.score ?? "-"}</strong>
        </div>
        <div className="metric">
          <span>Findings</span>
          <strong>{run.findings.length}</strong>
        </div>
        <div className="metric">
          <span>Trigger</span>
          <strong>
            <StatusBadge value={run.trigger_source} />
          </strong>
        </div>
        <div className="metric">
          <span>Head SHA</span>
          <strong>
            <code className="mono-value">{shortSha(run.head_sha)}</code>
          </strong>
        </div>
      </section>

      {run.error_message && <div className="error-banner">{run.error_message}</div>}

      {pullRequestContext && (
        <PullRequestContextPanel
          pullRequest={pullRequestContext}
          changedFiles={run.changed_files_snapshot_json}
        />
      )}

      <section className="panel">
        <div className="panel-header">
          <h2>Final Report</h2>
        </div>
        <pre className="markdown-block">{run.final_report_markdown}</pre>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Findings</h2>
        </div>
        <div className="finding-list">
          {run.findings.map((finding) => (
            <article className="finding-item" key={finding.id}>
              <div>
                <strong>{finding.title}</strong>
                <p>{finding.description}</p>
                <span>
                  {finding.file_path ?? "n/a"}
                  {finding.line_number ? `:${finding.line_number}` : ""}
                </span>
              </div>
              <div className="finding-meta">
                <StatusBadge value={finding.category} />
                <StatusBadge value={finding.severity} />
                <StatusBadge value={finding.blocking ? "blocking" : "warning"} />
              </div>
            </article>
          ))}
          {run.findings.length === 0 && <p>No findings.</p>}
        </div>
      </section>

      <section className="json-grid">
        <JsonPanel title="Coverage" value={run.coverage_result_json} />
        <JsonPanel title="Security" value={run.security_result_json} />
        <JsonPanel title="Technical Debt" value={run.technical_debt_result_json} />
      </section>
    </div>
  );
}

function PullRequestContextPanel({
  pullRequest,
  changedFiles
}: {
  pullRequest: PullRequestSnapshot;
  changedFiles: AnalysisRunDetail["changed_files_snapshot_json"];
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>Pull Request Context</h2>
          <p className="panel-subtitle">
            {changedFiles.length} changed {changedFiles.length === 1 ? "file" : "files"}
          </p>
        </div>
        <a href={pullRequest.html_url} rel="noreferrer" target="_blank">
          GitHub
        </a>
      </div>
      <div className="context-summary">
        <div>
          <span>Title</span>
          <strong>{pullRequest.title}</strong>
        </div>
        <div>
          <span>Author</span>
          <strong>{pullRequest.author_login}</strong>
        </div>
        <div>
          <span>Branches</span>
          <strong>
            {pullRequest.head_ref} → {pullRequest.base_ref}
          </strong>
        </div>
        <div>
          <span>Head SHA</span>
          <strong>
            <code className="mono-value">{shortSha(pullRequest.head_sha)}</code>
          </strong>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>File</th>
              <th>Status</th>
              <th>Additions</th>
              <th>Deletions</th>
              <th>Patch</th>
            </tr>
          </thead>
          <tbody>
            {changedFiles.map((file) => (
              <tr key={file.filename}>
                <td>
                  <code className="mono-value">{file.filename}</code>
                </td>
                <td>
                  <StatusBadge value={file.status} />
                </td>
                <td>{file.additions}</td>
                <td>{file.deletions}</td>
                <td>{file.patch ? "available" : "not available"}</td>
              </tr>
            ))}
            {changedFiles.length === 0 && (
              <tr>
                <td colSpan={5}>No changed files captured.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function hasPullRequestSnapshot(
  value: AnalysisRunDetail["pull_request_snapshot_json"]
): value is PullRequestSnapshot {
  return typeof value.number === "number" && typeof value.title === "string";
}

function shortSha(value: string) {
  return value.length > 12 ? value.slice(0, 12) : value;
}

function JsonPanel({
  title,
  value
}: {
  title: string;
  value: Record<string, unknown>;
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
      </div>
      <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>
    </section>
  );
}
