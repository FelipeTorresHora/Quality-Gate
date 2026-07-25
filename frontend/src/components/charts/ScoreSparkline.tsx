import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { DashboardRecentAnalysisRun } from "../../types/api";
import { chartColors } from "./chartColors";

const reduceMotion =
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

export default function ScoreSparkline({ runs }: { runs: DashboardRecentAnalysisRun[] }) {
  const scored = [...runs]
    .filter((run): run is DashboardRecentAnalysisRun & { score: number } => run.score !== null)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .map((run) => ({ label: `#${run.pr_number}`, score: run.score }));

  if (scored.length < 2) {
    return null;
  }

  return (
    <div className="chart-panel small">
      <ResponsiveContainer height="100%" width="100%">
        <AreaChart data={scored}>
          <defs>
            <linearGradient id="scoreFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={chartColors.accent} stopOpacity={0.35} />
              <stop offset="100%" stopColor={chartColors.accent} stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="label" hide />
          <YAxis domain={[0, 100]} hide />
          <Tooltip
            contentStyle={{
              background: chartColors.panel,
              border: `1px solid ${chartColors.border}`,
              borderRadius: 8,
              color: chartColors.text
            }}
          />
          <Area
            dataKey="score"
            fill="url(#scoreFill)"
            isAnimationActive={!reduceMotion}
            stroke={chartColors.accent}
            strokeWidth={2}
            type="monotone"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
