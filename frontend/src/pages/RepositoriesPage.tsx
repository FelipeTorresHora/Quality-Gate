import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  getGitHubInstallUrl,
  listGitHubInstallations,
  listRepositories
} from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import LoadingBlock from "../components/LoadingBlock";
import type { GitHubInstallation, Repository } from "../types/api";

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [installations, setInstallations] = useState<GitHubInstallation[]>([]);
  const [installUrl, setInstallUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    Promise.all([
      listRepositories(),
      listGitHubInstallations(),
      getGitHubInstallUrl()
    ])
      .then(([repositoryItems, installationItems, installUrlResult]) => {
        setRepositories(repositoryItems);
        setInstallations(installationItems);
        setInstallUrl(installUrlResult.url);
      })
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Repositories</p>
          <h1>GitHub Repositories</h1>
        </div>
        {installUrl && (
          <a className="button primary" href={installUrl}>
            Manage GitHub App
          </a>
        )}
      </header>

      <ErrorMessage error={error} />

      {loading ? (
        <LoadingBlock label="Loading repositories" />
      ) : repositories.length === 0 ? (
        <EmptyState
          action={
            installUrl ? (
              <a className="button primary" href={installUrl}>
                Install GitHub App
              </a>
            ) : null
          }
          title={
            installations.length === 0
              ? "No GitHub App installations"
              : "No accessible repositories"
          }
        >
          {installations.length === 0
            ? "Install the GitHub App to choose repositories for analysis."
            : "Update the GitHub App installation to grant repository access."}
        </EmptyState>
      ) : (
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Accessible Repositories</h2>
              <p className="panel-subtitle">
                {installations.length} active account installation
                {installations.length === 1 ? "" : "s"}
              </p>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Repository</th>
                  <th>Default branch</th>
                  <th>GitHub ID</th>
                </tr>
              </thead>
              <tbody>
                {repositories.map((repository) => (
                  <tr key={repository.id}>
                    <td>
                      <Link to={`/repositories/${repository.id}`}>
                        {repository.full_name}
                      </Link>
                    </td>
                    <td>{repository.default_branch}</td>
                    <td>{repository.github_repo_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
