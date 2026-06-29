import { useEffect, useState, type ReactNode } from "react";

import { getCurrentUser, getGitHubLoginUrl } from "../api/client";
import type { CurrentUser } from "../types/api";
import ErrorMessage from "./ErrorMessage";
import LoadingBlock from "./LoadingBlock";
import "./AuthGate.css";

export default function AuthGate({
  children
}: {
  children: (user: CurrentUser) => ReactNode;
}) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="auth-screen">
        <LoadingBlock label="Loading account" />
      </div>
    );
  }

  if (!user) {
    return (
      <main className="auth-screen">
        <div className="auth-panel">
          <div>
            <span className="brand-mark">QG</span>
            <p className="eyebrow">PR Quality Gate</p>
            <h1>Sign in to review Pull Requests</h1>
          </div>
          <ErrorMessage error={error} />
          <a className="button primary" href={getGitHubLoginUrl()}>
            Sign in with GitHub
          </a>
        </div>
      </main>
    );
  }

  return <>{children(user)}</>;
}
