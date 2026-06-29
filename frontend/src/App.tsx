import { Navigate, NavLink, Route, Routes } from "react-router-dom";

import { logout } from "./api/client";
import AuthGate from "./components/AuthGate";
import AnalysisDetailPage from "./pages/AnalysisDetailPage";
import DashboardPage from "./pages/DashboardPage";
import RepositoryAnalysisRunsPage from "./pages/RepositoryAnalysisRunsPage";
import RepositoryDetailPage from "./pages/RepositoryDetailPage";
import RepositoryPullRequestsPage from "./pages/RepositoryPullRequestsPage";
import RepositoryQualityGateConfigPage from "./pages/RepositoryQualityGateConfigPage";
import RepositoriesPage from "./pages/RepositoriesPage";
import type { CurrentUser } from "./types/api";

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
        <nav className="nav-list">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/repositories">Repositories</NavLink>
        </nav>
        <div className="user-chip">
          <span>{user.github_login}</span>
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
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/repositories" element={<RepositoriesPage />} />
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
      </main>
    </div>
  );
}
