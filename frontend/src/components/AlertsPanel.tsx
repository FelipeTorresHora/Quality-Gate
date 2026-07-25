import type { DashboardAlert } from "../lib/insights";

function AlertIcon({ severity }: { severity: DashboardAlert["severity"] | "ok" }) {
  if (severity === "ok") {
    return (
      <svg fill="none" height="18" viewBox="0 0 20 20" width="18">
        <path
          d="M4 10.5l3.5 3.5L16 5"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
        />
      </svg>
    );
  }
  return (
    <svg fill="none" height="18" viewBox="0 0 20 20" width="18">
      <path
        d="M10 2l9 16H1L10 2z"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.6"
      />
      <path d="M10 8v4" stroke="currentColor" strokeLinecap="round" strokeWidth="1.6" />
      <circle cx="10" cy="14.5" fill="currentColor" r="0.9" />
    </svg>
  );
}

export default function AlertsPanel({ alerts }: { alerts: DashboardAlert[] }) {
  if (alerts.length === 0) {
    return (
      <div className="alert-stack">
        <div className="alert severity-ok">
          <AlertIcon severity="ok" />
          <div>
            <p className="alert-title">All gates healthy</p>
            <p className="alert-detail">No approval-rate, error, or severity alerts right now.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="alert-stack">
      {alerts.map((alert) => (
        <div className={`alert severity-${alert.severity}`} key={alert.id}>
          <AlertIcon severity={alert.severity} />
          <div>
            <p className="alert-title">{alert.title}</p>
            <p className="alert-detail">{alert.detail}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
