import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getGitHubInstallUrl } from "../api/client";
import ErrorMessage from "../components/ErrorMessage";
import StatusBadge from "../components/StatusBadge";

export default function HelpPage() {
  const [installUrl, setInstallUrl] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    getGitHubInstallUrl()
      .then((result) => setInstallUrl(result.url))
      .catch(setError);
  }, []);

  return (
    <div className="page-stack animate-in">
      <header className="page-header">
        <div>
          <p className="eyebrow">Help</p>
          <h1>Get started</h1>
          <p className="page-lead">
            Connect the GitHub App to your repositories, then open or update a pull request to
            see the quality gate in GitHub and in this dashboard.
          </p>
        </div>
        {installUrl ? (
          <a className="button primary" href={installUrl}>
            Install GitHub App
          </a>
        ) : null}
      </header>

      <ErrorMessage error={error} />

      <div className="help-overview">
        <div className="help-step-card">
          <span className="help-step-num" aria-hidden="true">
            1
          </span>
          <strong>Install on repositories</strong>
          <p>Grant access to orgs or repos you want analyzed.</p>
        </div>
        <div className="help-step-card">
          <span className="help-step-num" aria-hidden="true">
            2
          </span>
          <strong>Verify your first PR</strong>
          <p>Watch the commit status and PR comment on a live pull request.</p>
        </div>
      </div>

      <section className="panel help-panel" id="install">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Step 1</p>
            <h2>Install on repositories</h2>
            <p className="panel-subtitle">
              Choose which accounts and repositories the GitHub App can access for analysis.
            </p>
          </div>
        </div>
        <ul className="help-checklist">
          <li>
            Open{" "}
            {installUrl ? (
              <a href={installUrl}>Install GitHub App</a>
            ) : (
              "Install GitHub App"
            )}{" "}
            or use the same action on the <Link to="/repositories">Repositories</Link> page.
          </li>
          <li>Select organizations or repositories and complete the GitHub installation flow.</li>
          <li>
            After sync, new repositories publish a PR comment and commit status by default (
            <code className="mono-value">comment_on_github</code> and{" "}
            <code className="mono-value">publish_github_status</code> are{" "}
            <code className="mono-value">true</code>). Status context is{" "}
            <code className="mono-value">ai-quality-gate</code>.
          </li>
        </ul>
        <p className="help-callout">
          This product does not register a required GitHub check, branch protection rule, or merge
          blocker — it publishes optional feedback only.
        </p>
        {installUrl ? (
          <div className="panel-actions">
            <a className="button primary" href={installUrl}>
              Install GitHub App
            </a>
            <Link className="button secondary" to="/repositories">
              Repositories
            </Link>
          </div>
        ) : null}
      </section>

      <section className="panel help-panel" id="verify">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Step 2</p>
            <h2>Verify the first pull request</h2>
            <p className="panel-subtitle">
              Open or update a PR on an installed repository to trigger analysis.
            </p>
          </div>
        </div>
        <div className="help-status-preview">
          <span className="help-status-label">Commit status context</span>
          <code className="mono-value">ai-quality-gate</code>
          <span className="help-status-arrow" aria-hidden="true">
            →
          </span>
          <StatusBadge value="pending" />
          <span className="help-status-arrow" aria-hidden="true">
            →
          </span>
          <StatusBadge value="pass" />
          <StatusBadge value="fail" />
          <StatusBadge value="error" />
        </div>
        <ul className="help-checklist">
          <li>
            On the PR, GitHub shows commit status{" "}
            <code className="mono-value">ai-quality-gate</code> as <strong>pending</strong> while
            the run executes.
          </li>
          <li>
            When the run finishes, the status becomes <strong>pass</strong>, <strong>fail</strong>,
            or <strong>error</strong>, with <code className="mono-value">target_url</code> linking
            to the analysis detail page in this dashboard.
          </li>
          <li>
            A PR comment is posted or updated with the quality gate summary when publishing is
            enabled for that repository.
          </li>
          <li>
            Track progress on the <Link to="/">Dashboard</Link> and under each repository&apos;s
            Pull Requests and Analysis History tabs.
          </li>
        </ul>
        <div className="panel-actions">
          <Link className="button primary" to="/">
            Open Dashboard
          </Link>
          <Link className="button secondary" to="/repositories">
            View repositories
          </Link>
        </div>
      </section>
    </div>
  );
}
