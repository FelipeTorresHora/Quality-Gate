import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  createMockAnalysisRun,
  getQualityGateConfig,
  getRepository,
  listAnalysisRuns,
  listPullRequests,
  updateQualityGateConfig
} from "../api/client";
import ErrorMessage from "../components/ErrorMessage";
import StatusBadge from "../components/StatusBadge";
import type {
  AnalysisRunSummary,
  GitHubPullRequest,
  MockScenario,
  QualityGateConfig,
  Repository
} from "../types/api";

const scenarios: MockScenario[] = [
  "passing",
  "coverage_fail",
  "security_fail",
  "technical_debt_fail",
  "mixed_fail"
];

export default function RepositoryDetailPage() {
  const { repositoryId } = useParams();
  const navigate = useNavigate();
  const [repository, setRepository] = useState<Repository | null>(null);
  const [config, setConfig] = useState<QualityGateConfig | null>(null);
  const [runs, setRuns] = useState<AnalysisRunSummary[]>([]);
  const [pullRequests, setPullRequests] = useState<GitHubPullRequest[]>([]);
  const [selectedScenario, setSelectedScenario] =
    useState<MockScenario>("mixed_fail");
  const [manualPrNumber, setManualPrNumber] = useState(1);
  const [manualHeadSha, setManualHeadSha] = useState("mock-head-sha");
  const [error, setError] = useState<unknown>(null);
  const [githubError, setGithubError] = useState<unknown>(null);

  useEffect(() => {
    if (!repositoryId) {
      return;
    }
    Promise.all([
      getRepository(repositoryId),
      getQualityGateConfig(repositoryId),
      listAnalysisRuns(repositoryId)
    ])
      .then(([repositoryData, configData, runData]) => {
        setRepository(repositoryData);
        setConfig(configData);
        setRuns(runData);
      })
      .catch(setError);

    listPullRequests(repositoryId)
      .then(setPullRequests)
      .catch(setGithubError);
  }, [repositoryId]);

  async function handleConfigSubmit(event: FormEvent) {
    event.preventDefault();
    if (!repositoryId || !config) {
      return;
    }
    setError(null);
    try {
      const updated = await updateQualityGateConfig(repositoryId, {
        min_total_coverage: config.min_total_coverage,
        max_coverage_drop: config.max_coverage_drop,
        min_changed_files_coverage: config.min_changed_files_coverage,
        security_fail_on: config.security_fail_on,
        max_function_lines: config.max_function_lines,
        max_complexity: config.max_complexity,
        fail_on_new_todo: config.fail_on_new_todo,
        comment_on_github: config.comment_on_github,
        publish_github_status: config.publish_github_status
      });
      setConfig(updated);
    } catch (caught) {
      setError(caught);
    }
  }

  async function createScenario(prNumber: number, headSha: string) {
    if (!repositoryId) {
      return;
    }
    setError(null);
    try {
      const run = await createMockAnalysisRun(repositoryId, {
        scenario: selectedScenario,
        pr_number: prNumber,
        head_sha: headSha
      });
      navigate(`/analysis-runs/${run.id}`);
    } catch (caught) {
      setError(caught);
    }
  }

  if (!repository || !config) {
    return (
      <div className="page-stack">
        <ErrorMessage error={error} />
      </div>
    );
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Repository</p>
          <h1>{repository.full_name}</h1>
        </div>
        <Link className="button" to="/repositories">
          Back
        </Link>
      </header>

      <ErrorMessage error={error} />

      <section className="split-layout">
        <div className="panel">
          <div className="panel-header">
            <h2>Quality Gate Config</h2>
          </div>
          <form className="settings-form" onSubmit={handleConfigSubmit}>
            <label>
              Min total coverage
              <input
                type="number"
                min="0"
                max="100"
                value={config.min_total_coverage}
                onChange={(event) =>
                  setConfig({
                    ...config,
                    min_total_coverage: Number(event.target.value)
                  })
                }
              />
            </label>
            <label>
              Max coverage drop
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={config.max_coverage_drop}
                onChange={(event) =>
                  setConfig({
                    ...config,
                    max_coverage_drop: Number(event.target.value)
                  })
                }
              />
            </label>
            <label>
              Changed files coverage
              <input
                type="number"
                min="0"
                max="100"
                value={config.min_changed_files_coverage}
                onChange={(event) =>
                  setConfig({
                    ...config,
                    min_changed_files_coverage: Number(event.target.value)
                  })
                }
              />
            </label>
            <label>
              Blocking severities
              <input
                value={
                  Array.isArray(config.security_fail_on)
                    ? config.security_fail_on.join(",")
                    : JSON.stringify(config.security_fail_on)
                }
                onChange={(event) =>
                  setConfig({
                    ...config,
                    security_fail_on: event.target.value
                      .split(",")
                      .map((item) => item.trim())
                      .filter(Boolean)
                  })
                }
              />
            </label>
            <label>
              Max function lines
              <input
                type="number"
                min="1"
                value={config.max_function_lines}
                onChange={(event) =>
                  setConfig({
                    ...config,
                    max_function_lines: Number(event.target.value)
                  })
                }
              />
            </label>
            <label>
              Max complexity
              <input
                type="number"
                min="1"
                value={config.max_complexity}
                onChange={(event) =>
                  setConfig({
                    ...config,
                    max_complexity: Number(event.target.value)
                  })
                }
              />
            </label>
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={config.fail_on_new_todo}
                onChange={(event) =>
                  setConfig({ ...config, fail_on_new_todo: event.target.checked })
                }
              />
              Fail on new TODO
            </label>
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={config.comment_on_github}
                onChange={(event) =>
                  setConfig({ ...config, comment_on_github: event.target.checked })
                }
              />
              Comment on GitHub
            </label>
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={config.publish_github_status}
                onChange={(event) =>
                  setConfig({
                    ...config,
                    publish_github_status: event.target.checked
                  })
                }
              />
              Publish GitHub status
            </label>
            <button className="button primary" type="submit">
              Save Config
            </button>
          </form>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Create Mock Analysis</h2>
          </div>
          <div className="form-grid single">
            <label>
              Scenario
              <select
                value={selectedScenario}
                onChange={(event) =>
                  setSelectedScenario(event.target.value as MockScenario)
                }
              >
                {scenarios.map((scenario) => (
                  <option key={scenario} value={scenario}>
                    {scenario}
                  </option>
                ))}
              </select>
            </label>
            <label>
              PR number
              <input
                type="number"
                min="1"
                value={manualPrNumber}
                onChange={(event) => setManualPrNumber(Number(event.target.value))}
              />
            </label>
            <label>
              Head SHA
              <input
                value={manualHeadSha}
                onChange={(event) => setManualHeadSha(event.target.value)}
              />
            </label>
            <button
              className="button primary"
              onClick={() => createScenario(manualPrNumber, manualHeadSha)}
              type="button"
            >
              Create Analysis
            </button>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Open Pull Requests</h2>
        </div>
        <ErrorMessage error={githubError} />
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>PR</th>
                <th>Title</th>
                <th>Branch</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {pullRequests.map((pullRequest) => (
                <tr key={pullRequest.number}>
                  <td>#{pullRequest.number}</td>
                  <td>
                    <a href={pullRequest.html_url} rel="noreferrer" target="_blank">
                      {pullRequest.title}
                    </a>
                  </td>
                  <td>
                    {pullRequest.head_ref} → {pullRequest.base_ref}
                  </td>
                  <td>
                    <button
                      className="button small"
                      onClick={() =>
                        createScenario(pullRequest.number, pullRequest.head_sha)
                      }
                      type="button"
                    >
                      Mock
                    </button>
                  </td>
                </tr>
              ))}
              {pullRequests.length === 0 && (
                <tr>
                  <td colSpan={4}>No open Pull Requests loaded.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Analysis History</h2>
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
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id}>
                  <td>
                    <Link to={`/analysis-runs/${run.id}`}>#{run.pr_number}</Link>
                  </td>
                  <td>
                    <StatusBadge value={run.status} />
                  </td>
                  <td>
                    <StatusBadge value={run.decision} />
                  </td>
                  <td>{run.score ?? "-"}</td>
                  <td>
                    <StatusBadge value={run.trigger_source} />
                  </td>
                  <td>
                    <code className="mono-value">{shortSha(run.head_sha)}</code>
                  </td>
                  <td>{new Date(run.created_at).toLocaleString()}</td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td colSpan={7}>No analysis runs yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function shortSha(value: string) {
  return value.length > 12 ? value.slice(0, 12) : value;
}
