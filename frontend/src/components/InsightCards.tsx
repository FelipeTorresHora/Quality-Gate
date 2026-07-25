import type { DashboardInsight } from "../lib/insights";

export default function InsightCards({ insights }: { insights: DashboardInsight[] }) {
  if (insights.length === 0) {
    return null;
  }

  return (
    <div className="insight-grid">
      {insights.map((insight) => (
        <div className="insight-card" key={insight.id}>
          <p className="eyebrow">{insight.label}</p>
          <span className={`insight-value${insight.tone ? ` tone-${insight.tone}` : ""}`}>
            {insight.value}
          </span>
          {insight.hint ? <p className="insight-hint">{insight.hint}</p> : null}
        </div>
      ))}
    </div>
  );
}
