import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import {
  executeAnalysisRun,
  getAnalysisRun,
  getQualityGateConfig,
  publishAnalysisRunToGitHub
} from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import LoadingBlock from "../components/LoadingBlock";
import StatusBadge from "../components/StatusBadge";
import type {
  AIReviewSnapshot,
  AnalysisRunDetail,
  GitHubPublicationResult,
  PullRequestSnapshot,
  QualityGateConfig
} from "../types/api";

export default function AnalysisDetailPage() {
  const { analysisRunId } = useParams();
  const [run, setRun] = useState<AnalysisRunDetail | null>(null);
  const [qualityConfig, setQualityConfig] = useState<QualityGateConfig | null>(null);
  const [publicationResult, setPublicationResult] =
    useState<GitHubPublicationResult | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [publishError, setPublishError] = useState<unknown>(null);
  const [retryError, setRetryError] = useState<unknown>(null);

  useEffect(() => {
    if (!analysisRunId) {
      return;
    }
    getAnalysisRun(analysisRunId)
      .then((analysisRun) => {
        setRun(analysisRun);
        return getQualityGateConfig(analysisRun.repository_id);
      })
      .then(setQualityConfig)
      .catch(setError);
  }, [analysisRunId]);

  useEffect(() => {
    if (!analysisRunId || !run) {
      return;
    }
    if (run.status !== "pending" && run.status !== "running") {
      return;
    }
    const timer = setTimeout(() => {
      getAnalysisRun(analysisRunId).then(setRun).catch(setError);
    }, 3000);
    return () => clearTimeout(timer);
  }, [analysisRunId, run]);

  if (error) {
    return (
      <div className="page-stack">
        <ErrorMessage error={error} />
      </div>
    );
  }

  if (!run) {
    return (
      <div className="page-stack">
        <LoadingBlock label="Loading Analysis Run" />
      </div>
    );
  }

  const pullRequestContext = hasPullRequestSnapshot(run.pull_request_snapshot_json)
    ? run.pull_request_snapshot_json
    : null;
  const canPublish = run.status === "completed" || run.status === "error";
  const runId = run.id;
  const publishingEnabled =
    Boolean(qualityConfig?.comment_on_github) ||
    Boolean(qualityConfig?.publish_github_status);

  async function handleRetry() {
    setRetrying(true);
    setRetryError(null);
    try {
      const updated = await executeAnalysisRun(runId);
      setRun(updated);
    } catch (caught) {
      setRetryError(caught);
    } finally {
      setRetrying(false);
    }
  }

  async function handlePublish() {
    setPublishing(true);
    setPublishError(null);
    try {
      const result = await publishAnalysisRunToGitHub(runId);
      setPublicationResult(result);
    } catch (caught) {
      setPublishError(caught);
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Analysis Run</p>
          <h1>PR #{run.pr_number}</h1>
        </div>
        <div className="header-actions">
          {run.status === "error" && (
            <button
              className="button primary"
              disabled={retrying}
              onClick={handleRetry}
              type="button"
            >
              {retrying ? "Re-running" : "Re-run Analysis"}
            </button>
          )}
          {canPublish && (
            <button
              className="button primary"
              disabled={!publishingEnabled || publishing}
              onClick={handlePublish}
              type="button"
            >
              {publishing ? "Publishing" : "Publish to GitHub"}
            </button>
          )}
          <Link className="button secondary" to={`/repositories/${run.repository_id}`}>
            Repository
          </Link>
        </div>
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
        <div className="metric">
          <span>Created</span>
          <strong>{new Date(run.created_at).toLocaleString()}</strong>
        </div>
      </section>

      <section className="metrics-grid four">
        <div className="metric">
          <span>PR Number</span>
          <strong>#{run.pr_number}</strong>
        </div>
        <div className="metric">
          <span>Started</span>
          <strong>{formatDate(run.started_at)}</strong>
        </div>
        <div className="metric">
          <span>Finished</span>
          <strong>{formatDate(run.finished_at)}</strong>
        </div>
        <div className="metric">
          <span>Findings</span>
          <strong>{run.findings.length}</strong>
        </div>
      </section>

      {run.error_message && <div className="error-banner">{run.error_message}</div>}
      {run.status === "error" && run.decision === null && (
        <div className="error-banner">
          Gate execution stopped because a required gate hit an operational error.
          Partial evidence below may be useful for diagnosis, but this run has no
          pass/fail quality decision.
        </div>
      )}
      {canPublish && !publishingEnabled && qualityConfig && (
        <div className="info-banner">
          GitHub publication is disabled for this repository.
        </div>
      )}
      {retryError ? <ErrorMessage error={retryError} /> : null}
      {publishError ? <ErrorMessage error={publishError} /> : null}
      {publicationResult && <PublicationResultPanel result={publicationResult} />}

      <AIReviewPanel value={run.ai_review_json} score={run.score} />

      {pullRequestContext && (
        <PullRequestContextPanel
          changedFiles={run.changed_files_snapshot_json}
          pullRequest={pullRequestContext}
        />
      )}

      <section className="pillar-grid">
        <PillarSummary title="Coverage" value={run.coverage_result_json} />
        <PillarSummary title="Security" value={run.security_result_json} />
        <PillarSummary title="Technical Debt" value={run.technical_debt_result_json} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Analysis Findings</h2>
        </div>
        {run.findings.length === 0 ? (
          <EmptyState title="No Analysis Findings">
            This run did not produce finding records.
          </EmptyState>
        ) : (
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
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Final Report</h2>
        </div>
        {run.final_report_markdown ? (
          <pre className="markdown-block">{run.final_report_markdown}</pre>
        ) : (
          <EmptyState title="No final report">
            This run has not generated a report.
          </EmptyState>
        )}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Diagnostic Snapshots</h2>
        </div>
        <div className="json-grid">
          <JsonPanel title="Coverage JSON" value={run.coverage_result_json} />
          <JsonPanel title="Security JSON" value={run.security_result_json} />
          <JsonPanel
            title="Technical Debt JSON"
            value={run.technical_debt_result_json}
          />
        </div>
      </section>
    </div>
  );
}

function AIReviewPanel({
  value,
  score
}: {
  value: AIReviewSnapshot;
  score: number | null;
}) {
  if (isGeneratedAIReview(value)) {
    return (
      <section className="panel ai-review-panel">
        <div className="panel-header">
          <div>
            <h2>AI Review</h2>
            <p className="panel-subtitle">{value.model}</p>
          </div>
          <div className="badge-row">
            <StatusBadge value={value.status} />
            <StatusBadge value={value.risk_level} />
          </div>
        </div>
        <div className="summary-copy">
          <p>{value.summary}</p>
        </div>
        <div className="metrics-grid four compact-metrics">
          <div className="metric">
            <span>AI Score</span>
            <strong>{score ?? value.score}</strong>
          </div>
          <div className="metric">
            <span>Risk</span>
            <strong>
              <StatusBadge value={value.risk_level} />
            </strong>
          </div>
          <div className="metric">
            <span>Blockers</span>
            <strong>{value.blocking_reasons.length}</strong>
          </div>
          <div className="metric">
            <span>Suggestions</span>
            <strong>{value.suggestions.length}</strong>
          </div>
        </div>
        <div className="ai-assessments">
          <p>{value.coverage_assessment}</p>
          <p>{value.security_assessment}</p>
          <p>{value.technical_debt_assessment}</p>
        </div>
        {value.suggestions.length > 0 && (
          <div className="note-list muted">
            {value.suggestions.map((suggestion) => (
              <p key={suggestion}>{suggestion}</p>
            ))}
          </div>
        )}
      </section>
    );
  }

  if (isSkippedAIReview(value)) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2>AI Review</h2>
          <StatusBadge value={value.status} />
        </div>
        <div className="summary-copy">
          <p>AI review was skipped because OpenAI is not configured.</p>
        </div>
      </section>
    );
  }

  if (isErroredAIReview(value)) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2>AI Review</h2>
          <StatusBadge value={value.status} />
        </div>
        <div className="summary-copy">
          <p>{value.message}</p>
        </div>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>AI Review</h2>
        <StatusBadge value="none" />
      </div>
      <EmptyState title="No AI review">
        This run does not have an AI review snapshot.
      </EmptyState>
    </section>
  );
}

function PublicationResultPanel({ result }: { result: GitHubPublicationResult }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>GitHub Publication</h2>
        <StatusBadge value="published" />
      </div>
      <div className="summary-list">
        <PublicationRow
          label="Pull Request Comment"
          published={result.comment.published}
          skippedReason={result.comment.skipped_reason}
          value={
            result.comment.html_url ? (
              <a href={result.comment.html_url} rel="noreferrer" target="_blank">
                Comment
              </a>
            ) : null
          }
        />
        <PublicationRow
          label="Commit Status"
          published={result.commit_status.published}
          skippedReason={result.commit_status.skipped_reason}
          value={
            result.commit_status.state ? (
              <StatusBadge value={result.commit_status.state} />
            ) : null
          }
        />
      </div>
    </section>
  );
}

function PublicationRow({
  label,
  published,
  skippedReason,
  value
}: {
  label: string;
  published: boolean;
  skippedReason: string | null;
  value: ReactNode;
}) {
  return (
    <div className="summary-row">
      <span>{label}</span>
      <strong>
        {published ? value ?? "published" : skippedReason ?? "skipped"}
      </strong>
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
          <h2>Pull Request Snapshot</h2>
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
            {pullRequest.head_ref} to {pullRequest.base_ref}
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

function PillarSummary({
  title,
  value
}: {
  title: string;
  value: Record<string, unknown>;
}) {
  const blockingReasons = stringArray(value.blocking_reasons);
  const suggestions = stringArray(value.suggestions);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>{title}</h2>
          <p className="panel-subtitle">{displayValue(value.status) || "not reported"}</p>
        </div>
        <StatusBadge value={stringValue(value.status) ?? "none"} />
      </div>
      <div className="summary-list">
        {summaryEntries(title, value).map((entry) => (
          <div className="summary-row" key={entry.label}>
            <span>{entry.label}</span>
            <strong>{entry.value}</strong>
          </div>
        ))}
      </div>
      {blockingReasons.length > 0 && (
        <div className="note-list">
          {blockingReasons.map((reason) => (
            <p key={reason}>{reason}</p>
          ))}
        </div>
      )}
      {suggestions.length > 0 && (
        <div className="note-list muted">
          {suggestions.map((suggestion) => (
            <p key={suggestion}>{suggestion}</p>
          ))}
        </div>
      )}
    </section>
  );
}

function summaryEntries(title: string, value: Record<string, unknown>) {
  if (title === "Coverage") {
    return [
      { label: "Language", value: displayValue(value.language) },
      { label: "Report format", value: displayValue(value.report_format) },
      { label: "Base SHA", value: displayValue(value.base_sha) },
      { label: "Head SHA", value: displayValue(value.head_sha) },
      { label: "Total", value: displayValue(value.total_coverage) },
      { label: "Base", value: displayValue(value.base_coverage) },
      { label: "PR", value: displayValue(value.pr_coverage) },
      { label: "Changed files", value: displayValue(value.changed_files_coverage) },
      { label: "Drop", value: displayValue(value.coverage_drop) },
      {
        label: "Changed source files",
        value: String(arrayValue(value.changed_source_files).length),
      },
      {
        label: "Commands",
        value: String(arrayValue(value.commands).length),
      },
    ].filter((entry) => entry.value !== "");
  }

  if (title === "Security") {
    return [
      {
        label: "Scanners",
        value: arrayValue(value.scanners_run).join(", "),
      },
      { label: "Critical", value: displayValue(value.critical) },
      { label: "High", value: displayValue(value.high) },
      { label: "Medium", value: displayValue(value.medium) },
      { label: "Low", value: displayValue(value.low) },
      {
        label: "Warnings",
        value: String(arrayValue(value.warnings).length),
      },
    ].filter((entry) => entry.value !== "");
  }

  return [
    { label: "New TODO/FIXME", value: displayValue(value.new_todo_count) },
    { label: "Function length", value: displayValue(value.function_length_count) },
    { label: "Complexity", value: displayValue(value.complexity_count) },
    {
      label: "Blocking reasons",
      value: String(stringArray(value.blocking_reasons).length),
    },
    { label: "Suggestions", value: String(stringArray(value.suggestions).length) },
  ];
}

function JsonPanel({
  title,
  value
}: {
  title: string;
  value: Record<string, unknown>;
}) {
  return (
    <section className="json-panel">
      <h3>{title}</h3>
      <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>
    </section>
  );
}

function hasPullRequestSnapshot(
  value: AnalysisRunDetail["pull_request_snapshot_json"]
): value is PullRequestSnapshot {
  return typeof value.number === "number" && typeof value.title === "string";
}

function isGeneratedAIReview(value: AIReviewSnapshot): value is Extract<
  AIReviewSnapshot,
  { status: "generated" }
> {
  return "status" in value && value.status === "generated";
}

function isSkippedAIReview(value: AIReviewSnapshot): value is Extract<
  AIReviewSnapshot,
  { status: "skipped" }
> {
  return "status" in value && value.status === "skipped";
}

function isErroredAIReview(value: AIReviewSnapshot): value is Extract<
  AIReviewSnapshot,
  { status: "error" }
> {
  return "status" in value && value.status === "error";
}

function stringArray(value: unknown) {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function arrayValue(value: unknown) {
  return Array.isArray(value) ? value : [];
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value : null;
}

function displayValue(value: unknown) {
  if (typeof value === "number") {
    return String(value);
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return "";
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "-";
}

function shortSha(value: string) {
  return value.length > 12 ? value.slice(0, 12) : value;
}
