import { lazy, Suspense } from "react";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";

import { logout } from "./api/client";
import AuthGate from "./components/AuthGate";
import PageFallback from "./components/PageFallback";
import type { CurrentUser } from "./types/api";

const AnalysisDetailPage = lazy(() => import("./pages/AnalysisDetailPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const HelpPage = lazy(() => import("./pages/HelpPage"));
const RepositoriesPage = lazy(() => import("./pages/RepositoriesPage"));
const RepositoryAnalysisRunsPage = lazy(() => import("./pages/RepositoryAnalysisRunsPage"));
const RepositoryDetailPage = lazy(() => import("./pages/RepositoryDetailPage"));
const RepositoryPullRequestsPage = lazy(() => import("./pages/RepositoryPullRequestsPage"));
const RepositoryQualityGateConfigPage = lazy(
  () => import("./pages/RepositoryQualityGateConfigPage")
);

export default function App() {
  return <AuthGate>{(user) => <AuthenticatedApp user={user} />}</AuthGate>;
}

function AuthenticatedApp({ user }: { user: CurrentUser }) {
  async function handleLogout() {
    await logout();
    window.location.assign("/");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">QG</span>
          <span>PR Quality Gate</span>
        </div>
        <p className="eyebrow">Navigation</p>
        <nav className="nav-list">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/repositories">Repositories</NavLink>
          <NavLink to="/help">Help</NavLink>
        </nav>
        <div className="user-chip">
          {user.avatar_url ? (
            <img alt="" className="user-avatar" src={user.avatar_url} />
          ) : (
            <span className="user-avatar user-avatar-fallback">
              {user.github_login.slice(0, 1).toUpperCase()}
            </span>
          )}
          <span className="user-login">{user.github_login}</span>
          <button
            className="button small secondary"
            onClick={handleLogout}
            type="button"
          >
            Sign out
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/repositories" element={<RepositoriesPage />} />
            <Route path="/help" element={<HelpPage />} />
            <Route path="/repositories/:repositoryId" element={<RepositoryDetailPage />}>
              <Route index element={<Navigate replace to="pull-requests" />} />
              <Route path="pull-requests" element={<RepositoryPullRequestsPage />} />
              <Route
                path="quality-gate-config"
                element={<RepositoryQualityGateConfigPage />}
              />
              <Route path="analysis-runs" element={<RepositoryAnalysisRunsPage />} />
            </Route>
            <Route path="/analysis-runs/:analysisRunId" element={<AnalysisDetailPage />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}
