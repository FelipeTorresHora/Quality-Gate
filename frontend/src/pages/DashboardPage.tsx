import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getHealth, listRepositories } from "../api/client";
import ErrorMessage from "../components/ErrorMessage";
import type { Repository } from "../types/api";

export default function DashboardPage() {
  const [apiStatus, setApiStatus] = useState("checking");
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    Promise.all([getHealth(), listRepositories()])
      .then(([health, repositoryList]) => {
        setApiStatus(health.status);
        setRepositories(repositoryList);
      })
      .catch(setError);
  }, []);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Foundation</p>
          <h1>PR Quality Gate Dashboard</h1>
        </div>
        <Link className="button primary" to="/repositories">
          Repositories
        </Link>
      </header>

      <ErrorMessage error={error} />

      <section className="metrics-grid">
        <div className="metric">
          <span>API Status</span>
          <strong>{apiStatus}</strong>
        </div>
        <div className="metric">
          <span>Repositories</span>
          <strong>{repositories.length}</strong>
        </div>
        <div className="metric">
          <span>Gate Pillars</span>
          <strong>3</strong>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Recent Repositories</h2>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Default branch</th>
                <th>Updated</th>
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
                  <td>{new Date(repository.updated_at).toLocaleString()}</td>
                </tr>
              ))}
              {repositories.length === 0 && (
                <tr>
                  <td colSpan={3}>No repositories registered.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
