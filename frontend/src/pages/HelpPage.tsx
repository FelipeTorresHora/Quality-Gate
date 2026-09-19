import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getGitHubInstallUrl } from "../api/client";
import ErrorMessage from "../components/ErrorMessage";

export default function HelpPage() {
  const [installUrl, setInstallUrl] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    getGitHubInstallUrl()
      .then((result) => setInstallUrl(result.url))
      .catch(setError);
  }, []);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Help</p>
          <h1>Production setup</h1>
          <p className="page-lead">
            Register the GitHub App, deploy the dashboard, and install the bot on repositories.
            Sign-in and analysis use GitHub App installations and OAuth only — there is no mock
            analysis or manual repository creation.
          </p>
        </div>
        {installUrl && (
          <a className="button primary" href={installUrl}>
            Install GitHub App
          </a>
        )}
      </header>

      <ErrorMessage error={error} />

      <section className="panel help-panel">
        <div className="panel-header">
          <div>
            <h2>1. Create the GitHub App</h2>
            <p className="panel-subtitle">
              In GitHub → Settings → Developer settings → GitHub Apps → New GitHub App.
            </p>
          </div>
        </div>
        <ol className="help-steps">
          <li>
            Set <strong>Homepage URL</strong> to your public frontend origin (for example{" "}
            <code className="mono-value">https://app.example.com</code>).
          </li>
          <li>
            Set the OAuth <strong>Callback URL</strong> to{" "}
            <code className="mono-value">
              {"{public-backend-url}"}/api/auth/github/callback
            </code>
            .
          </li>
          <li>
            Enable the <strong>Webhook</strong> with URL{" "}
            <code className="mono-value">{"{public-backend-url}"}/api/github/webhooks</code> and a
            strong secret (store it as <code className="mono-value">GITHUB_WEBHOOK_SECRET</code>).
          </li>
          <li>
            <strong>Repository permissions:</strong> Metadata (read), Contents (read), Pull
            requests (write), Commit statuses (write).
          </li>
          <li>
            <strong>Subscribe to events:</strong> <code className="mono-value">pull_request</code>
            , <code className="mono-value">installation</code>,{" "}
            <code className="mono-value">installation_repositories</code>, and GitHub App
            authorization.
          </li>
          <li>Generate a private key and note the App ID, Client ID, and Client secret.</li>
        </ol>
      </section>

      <section className="panel help-panel">
        <div className="panel-header">
          <div>
            <h2>2. Configure production environment</h2>
            <p className="panel-subtitle">
              Set these on the backend API and worker (same values on both).
            </p>
          </div>
        </div>
        <ul className="help-env-list">
          <li>
            <code className="mono-value">GITHUB_APP_ID</code>,{" "}
            <code className="mono-value">GITHUB_APP_CLIENT_ID</code>,{" "}
            <code className="mono-value">GITHUB_APP_CLIENT_SECRET</code>
          </li>
          <li>
            <code className="mono-value">GITHUB_APP_PRIVATE_KEY</code> (or{" "}
            <code className="mono-value">GITHUB_APP_PRIVATE_KEY_PATH</code>)
          </li>
          <li>
            <code className="mono-value">GITHUB_APP_SLUG</code>,{" "}
            <code className="mono-value">GITHUB_WEBHOOK_SECRET</code>
          </li>
          <li>
            <code className="mono-value">SESSION_SECRET</code> (32+ random bytes),{" "}
            <code className="mono-value">TOKEN_ENCRYPTION_KEY</code>
          </li>
          <li>
            <code className="mono-value">FRONTEND_ORIGIN</code>,{" "}
            <code className="mono-value">DATABASE_URL</code>,{" "}
            <code className="mono-value">AUTH_CALLBACK_URL</code> (HTTPS callback in production)
          </li>
          <li>
            Optional AI tracing: <code className="mono-value">OPENAI_API_KEY</code>,{" "}
            <code className="mono-value">LANGSMITH_TRACING</code>,{" "}
            <code className="mono-value">LANGSMITH_API_KEY</code>,{" "}
            <code className="mono-value">LANGSMITH_PROJECT</code>
          </li>
        </ul>
        <p className="help-footnote">
          Set <code className="mono-value">VITE_API_BASE_URL</code> on the frontend build to your
          public backend URL. Use <code className="mono-value">SESSION_COOKIE_SECURE=true</code>{" "}
          when auth runs over HTTPS.
        </p>
      </section>

      <section className="panel help-panel">
        <div className="panel-header">
          <div>
            <h2>3. Deploy backend, frontend, and worker</h2>
            <p className="panel-subtitle">
              Postgres must be reachable; the API runs migrations on startup.
            </p>
          </div>
        </div>
        <ol className="help-steps">
          <li>
            Deploy the FastAPI backend (webhooks and OAuth callback must be publicly reachable).
          </li>
          <li>
            Deploy the analysis worker process (for example{" "}
            <code className="mono-value">python -m app.worker</code> in Docker Compose).
          </li>
          <li>Deploy the Vite frontend with the production API base URL.</li>
          <li>
            Confirm <code className="mono-value">GET /health</code> returns OK and GitHub App
            credentials validate.
          </li>
        </ol>
      </section>

      <section className="panel help-panel">
        <div className="panel-header">
          <div>
            <h2>4. Install on repositories</h2>
            <p className="panel-subtitle">
              Grant access to orgs or repos you want analyzed (including this product repo if you
              dogfood here).
            </p>
          </div>
        </div>
        <ol className="help-steps">
          <li>
            Use{" "}
            {installUrl ? (
              <a href={installUrl}>Install GitHub App</a>
            ) : (
              "Install GitHub App"
            )}{" "}
            or the button on the{" "}
            <Link to="/repositories">Repositories</Link> page.
          </li>
          <li>Choose accounts and repositories, then complete the GitHub installation flow.</li>
          <li>
            After sync, new repositories default to publishing a PR comment and commit status (
            <code className="mono-value">comment_on_github</code> and{" "}
            <code className="mono-value">publish_github_status</code> are{" "}
            <code className="mono-value">true</code>). Status context is{" "}
            <code className="mono-value">ai-quality-gate</code>.
          </li>
          <li>
            This product does not register a required GitHub check, branch protection rule, or merge
            blocker — it publishes optional feedback only.
          </li>
        </ol>
      </section>

      <section className="panel help-panel">
        <div className="panel-header">
          <div>
            <h2>5. Verify the first pull request</h2>
            <p className="panel-subtitle">
              Open or update a PR on an installed repository to trigger analysis.
            </p>
          </div>
        </div>
        <ol className="help-steps">
          <li>
            On the PR, GitHub should show a commit status in context{" "}
            <code className="mono-value">ai-quality-gate</code> moving from{" "}
            <strong>pending</strong> while the run executes.
          </li>
          <li>
            When the run finishes, the status becomes <strong>pass</strong>, <strong>fail</strong>,
            or <strong>error</strong>, with <code className="mono-value">target_url</code> linking
            to the analysis detail page in this dashboard.
          </li>
          <li>
            A PR comment is posted or updated with the quality gate summary (when publishing is
            enabled for that repository).
          </li>
          <li>
            Track progress on the <Link to="/">Dashboard</Link> and under each repository&apos;s
            Pull Requests and Analysis History tabs.
          </li>
        </ol>
      </section>
    </div>
  );
}
