import { FormEvent, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";

import {
  getCoverageExecutionConfig,
  getQualityGateConfig,
  updateCoverageExecutionConfig,
  updateQualityGateConfig
} from "../api/client";
import ErrorMessage from "../components/ErrorMessage";
import LoadingBlock from "../components/LoadingBlock";
import type { RepositoryWorkspaceContext } from "./RepositoryDetailPage";
import type { CoverageExecutionConfig, QualityGateConfig } from "../types/api";

export default function RepositoryQualityGateConfigPage() {
  const { repository } = useOutletContext<RepositoryWorkspaceContext>();
  const [config, setConfig] = useState<QualityGateConfig | null>(null);
  const [coverageExecutionConfig, setCoverageExecutionConfig] =
    useState<CoverageExecutionConfig | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [coverageExecutionError, setCoverageExecutionError] =
    useState<unknown>(null);

  useEffect(() => {
    setError(null);
    setCoverageExecutionError(null);
    getQualityGateConfig(repository.id).then(setConfig).catch(setError);
    getCoverageExecutionConfig(repository.id)
      .then(setCoverageExecutionConfig)
      .catch(setCoverageExecutionError);
  }, [repository.id]);

  async function handleCoverageExecutionSubmit(event: FormEvent) {
    event.preventDefault();
    if (!coverageExecutionConfig) {
      return;
    }
    setCoverageExecutionError(null);
    try {
      const updated = await updateCoverageExecutionConfig(repository.id, {
        language: coverageExecutionConfig.language,
        install_command: coverageExecutionConfig.install_command,
        test_command: coverageExecutionConfig.test_command,
        report_path: coverageExecutionConfig.report_path,
        report_format: coverageExecutionConfig.report_format
      });
      setCoverageExecutionConfig(updated);
    } catch (caught) {
      setCoverageExecutionError(caught);
    }
  }

  async function handleConfigSubmit(event: FormEvent) {
    event.preventDefault();
    if (!config) {
      return;
    }
    setError(null);
    try {
      const updated = await updateQualityGateConfig(repository.id, {
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

  if (!config || !coverageExecutionConfig) {
    return (
      <div className="page-stack">
        <ErrorMessage error={error} />
        <ErrorMessage error={coverageExecutionError} />
        <LoadingBlock label="Loading Repository Config" />
      </div>
    );
  }

  return (
    <div className="page-stack">
      <ErrorMessage error={error} />
      <ErrorMessage error={coverageExecutionError} />

      <form className="page-stack" onSubmit={handleCoverageExecutionSubmit}>
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Coverage Execution</h2>
              <p className="panel-subtitle">
                Commands and report location used before applying coverage policy.
              </p>
            </div>
          </div>
          <div className="settings-form">
            <label>
              Language
              <select
                value={coverageExecutionConfig.language}
                onChange={(event) =>
                  setCoverageExecutionConfig({
                    ...coverageExecutionConfig,
                    language: event.target.value as CoverageExecutionConfig["language"],
                    report_format: defaultReportFormat(
                      event.target.value as CoverageExecutionConfig["language"]
                    )
                  })
                }
              >
                <option value="python">python</option>
                <option value="typescript">typescript</option>
                <option value="javascript">javascript</option>
                <option value="go">go</option>
              </select>
            </label>
            <label>
              Install command
              <input
                value={coverageExecutionConfig.install_command}
                onChange={(event) =>
                  setCoverageExecutionConfig({
                    ...coverageExecutionConfig,
                    install_command: event.target.value
                  })
                }
              />
            </label>
            <label>
              Test command
              <input
                value={coverageExecutionConfig.test_command}
                onChange={(event) =>
                  setCoverageExecutionConfig({
                    ...coverageExecutionConfig,
                    test_command: event.target.value
                  })
                }
              />
            </label>
            <label>
              Report path
              <input
                value={coverageExecutionConfig.report_path}
                onChange={(event) =>
                  setCoverageExecutionConfig({
                    ...coverageExecutionConfig,
                    report_path: event.target.value
                  })
                }
              />
            </label>
            <label>
              Report format
              <select
                value={coverageExecutionConfig.report_format}
                onChange={(event) =>
                  setCoverageExecutionConfig({
                    ...coverageExecutionConfig,
                    report_format: event.target
                      .value as CoverageExecutionConfig["report_format"]
                  })
                }
              >
                <option value="cobertura_xml">cobertura_xml</option>
                <option value="lcov">lcov</option>
                <option value="go_coverprofile">go_coverprofile</option>
              </select>
            </label>
          </div>
          <div className="form-actions panel-actions">
            <button className="button primary" type="submit">
              Save Coverage Execution
            </button>
          </div>
        </section>
      </form>

      <form className="page-stack" onSubmit={handleConfigSubmit}>
        <section className="panel">
          <div className="panel-header">
            <h2>Coverage</h2>
          </div>
          <div className="settings-form">
            <label>
              Minimum total coverage
              <input
                max="100"
                min="0"
                type="number"
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
              Maximum coverage drop
              <input
                max="100"
                min="0"
                step="0.1"
                type="number"
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
              Minimum changed-files coverage
              <input
                max="100"
                min="0"
                type="number"
                value={config.min_changed_files_coverage}
                onChange={(event) =>
                  setConfig({
                    ...config,
                    min_changed_files_coverage: Number(event.target.value)
                  })
                }
              />
            </label>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Security</h2>
          </div>
          <div className="settings-form">
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
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Technical Debt</h2>
          </div>
          <div className="settings-form">
            <label>
              Max function lines
              <input
                min="1"
                type="number"
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
                min="1"
                type="number"
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
                checked={config.fail_on_new_todo}
                type="checkbox"
                onChange={(event) =>
                  setConfig({ ...config, fail_on_new_todo: event.target.checked })
                }
              />
              Fail on new TODO
            </label>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>GitHub Publishing</h2>
          </div>
          <div className="settings-form">
            <label className="checkbox-line">
              <input
                checked={config.comment_on_github}
                type="checkbox"
                onChange={(event) =>
                  setConfig({ ...config, comment_on_github: event.target.checked })
                }
              />
              Comment on GitHub
            </label>
            <label className="checkbox-line">
              <input
                checked={config.publish_github_status}
                type="checkbox"
                onChange={(event) =>
                  setConfig({
                    ...config,
                    publish_github_status: event.target.checked
                  })
                }
              />
              Publish GitHub status
            </label>
          </div>
        </section>

        <div className="form-actions">
          <button className="button primary" type="submit">
            Save Quality Gate Policy
          </button>
        </div>
      </form>
    </div>
  );
}

function defaultReportFormat(
  language: CoverageExecutionConfig["language"]
): CoverageExecutionConfig["report_format"] {
  if (language === "go") {
    return "go_coverprofile";
  }
  if (language === "python") {
    return "cobertura_xml";
  }
  return "lcov";
}
