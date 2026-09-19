import { useCallback, useEffect, useState } from "react";
import { Link, NavLink, Outlet, useParams } from "react-router-dom";

import { getRepository, listAnalysisRuns } from "../api/client";
import ErrorMessage from "../components/ErrorMessage";
import LoadingBlock from "../components/LoadingBlock";
import RunTicker from "../components/RunTicker";
import StatusBadge from "../components/StatusBadge";
import type { AnalysisRunSummary, Repository } from "../types/api";

export type RepositoryWorkspaceContext = {
  repository: Repository;
  runs: AnalysisRunSummary[];
  refreshRuns: () => Promise<void>;
};

export default function RepositoryDetailPage() {
  const { repositoryId } = useParams();
  const [repository, setRepository] = useState<Repository | null>(null);
  const [runs, setRuns] = useState<AnalysisRunSummary[]>([]);
  const [error, setError] = useState<unknown>(null);

  const refreshRuns = useCallback(() => {
    if (!repositoryId) {
      return Promise.resolve();
    }
    return listAnalysisRuns(repositoryId)
      .then(setRuns)
      .catch(() => setRuns([]));
  }, [repositoryId]);

  useEffect(() => {
    if (!repositoryId) {
      return;
    }
    setError(null);
    getRepository(repositoryId).then(setRepository).catch(setError);
    refreshRuns();
  }, [repositoryId, refreshRuns]);

  if (error) {
    return (
      <div className="page-stack">
        <ErrorMessage error={error} />
      </div>
    );
  }

  if (!repository) {
    return (
      <div className="page-stack">
        <LoadingBlock label="Loading repository" />
      </div>
    );
  }

  return (
    <div className="page-stack">
      <header className="workspace-header">
        <div>
          <p className="eyebrow">Repository</p>
          <h1>{repository.full_name}</h1>
          <div className="workspace-meta">
            <span>Default branch: {repository.default_branch}</span>
            <StatusBadge value="github" />
          </div>
        </div>
        <Link className="button secondary" to="/repositories">
          Repositories
        </Link>
      </header>

      {runs.length > 0 && (
        <RunTicker
          getLabel={(run) => `#${run.pr_number} · ${run.decision ?? run.status}`}
          runs={runs}
        />
      )}

      <nav className="workspace-tabs">
        <NavLink to="pull-requests">Pull Requests</NavLink>
        <NavLink to="quality-gate-config">Quality Gate Config</NavLink>
        <NavLink to="analysis-runs">Analysis History</NavLink>
      </nav>

      <Outlet
        context={{ repository, runs, refreshRuns } satisfies RepositoryWorkspaceContext}
      />
    </div>
  );
}
