import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import type { DashboardFindingCount } from "../../types/api";
import { chartColors } from "./chartColors";

const SEVERITY_ORDER = ["low", "medium", "high", "critical"] as const;
const SEVERITY_COLOR: Record<(typeof SEVERITY_ORDER)[number], string> = {
  low: chartColors.pass,
  medium: chartColors.warn,
  high: "#fb923c",
  critical: chartColors.fail
};

const reduceMotion =
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

export default function FindingsBar({
  findingCounts
}: {
  findingCounts: DashboardFindingCount[];
}) {
  if (findingCounts.length === 0) {
    return null;
  }

  const byCategory = new Map<string, Record<string, number> & { category: string }>();
  for (const item of findingCounts) {
    const row =
      byCategory.get(item.category) ??
      ({ category: item.category } as Record<string, number> & { category: string });
    row[item.severity] = item.count;
    byCategory.set(item.category, row);
  }
  const data = [...byCategory.values()];

  return (
    <div className="chart-panel">
      <ResponsiveContainer height="100%" width="100%">
        <BarChart data={data}>
          <CartesianGrid stroke={chartColors.border} vertical={false} />
          <XAxis
            dataKey="category"
            stroke={chartColors.muted}
            tick={{ fill: chartColors.muted, fontSize: 12 }}
            tickLine={false}
          />
          <YAxis
            allowDecimals={false}
            stroke={chartColors.muted}
            tick={{ fill: chartColors.muted, fontSize: 12 }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: chartColors.panel,
              border: `1px solid ${chartColors.border}`,
              borderRadius: 8,
              color: chartColors.text
            }}
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
          />
          <Legend wrapperStyle={{ color: chartColors.muted, fontSize: 12 }} />
          {SEVERITY_ORDER.map((severity) => (
            <Bar
              dataKey={severity}
              fill={SEVERITY_COLOR[severity]}
              isAnimationActive={!reduceMotion}
              key={severity}
              radius={severity === "critical" ? [4, 4, 0, 0] : undefined}
              stackId="severity"
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
