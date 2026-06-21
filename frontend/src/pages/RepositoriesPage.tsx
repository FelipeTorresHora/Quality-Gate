import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  createGitHubRepository,
  createRepository,
  listRepositories
} from "../api/client";
import ErrorMessage from "../components/ErrorMessage";
import type { Repository } from "../types/api";

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [owner, setOwner] = useState("");
  const [name, setName] = useState("");
  const [defaultBranch, setDefaultBranch] = useState("main");
  const [mode, setMode] = useState<"manual" | "github">("manual");
  const [error, setError] = useState<unknown>(null);

  function refresh() {
    listRepositories().then(setRepositories).catch(setError);
  }

  useEffect(refresh, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      if (mode === "github") {
        await createGitHubRepository({ owner, name });
      } else {
        await createRepository({
          owner,
          name,
          full_name: `${owner}/${name}`,
          default_branch: defaultBranch
        });
      }
      setOwner("");
      setName("");
      setDefaultBranch("main");
      refresh();
    } catch (caught) {
      setError(caught);
    }
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Repositories</p>
          <h1>Repository Registry</h1>
        </div>
      </header>

      <ErrorMessage error={error} />

      <section className="panel">
        <div className="panel-header">
          <h2>Create Repository</h2>
          <div className="segmented">
            <button
              className={mode === "manual" ? "active" : ""}
              onClick={() => setMode("manual")}
              type="button"
            >
              Manual
            </button>
            <button
              className={mode === "github" ? "active" : ""}
              onClick={() => setMode("github")}
              type="button"
            >
              GitHub
            </button>
          </div>
        </div>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Owner
            <input
              value={owner}
              onChange={(event) => setOwner(event.target.value)}
              required
            />
          </label>
          <label>
            Name
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </label>
          {mode === "manual" && (
            <label>
              Default branch
              <input
                value={defaultBranch}
                onChange={(event) => setDefaultBranch(event.target.value)}
                required
              />
            </label>
          )}
          <button className="button primary" type="submit">
            Create
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Registered Repositories</h2>
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
                  <td>{repository.github_repo_id ?? "manual"}</td>
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
