import { Navigate, NavLink, Route, Routes } from "react-router-dom";

import AnalysisDetailPage from "./pages/AnalysisDetailPage";
import DashboardPage from "./pages/DashboardPage";
import RepositoryAnalysisRunsPage from "./pages/RepositoryAnalysisRunsPage";
import RepositoryDetailPage from "./pages/RepositoryDetailPage";
import RepositoryPullRequestsPage from "./pages/RepositoryPullRequestsPage";
import RepositoryQualityGateConfigPage from "./pages/RepositoryQualityGateConfigPage";
import RepositoriesPage from "./pages/RepositoriesPage";

export default function App() {
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
