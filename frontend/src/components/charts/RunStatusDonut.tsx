import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { AnalysisRunSummary } from "../../types/api";
import { chartColors } from "./chartColors";

type RunStatusDonutProps = {
  counts: Record<AnalysisRunSummary["status"], number>;
};

const STATUS_COLOR: Record<AnalysisRunSummary["status"], string> = {
  completed: chartColors.pass,
  error: chartColors.fail,
  running: chartColors.warn,
  pending: chartColors.neutral
};

const reduceMotion =
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

export default function RunStatusDonut({ counts }: RunStatusDonutProps) {
  const data = (Object.keys(counts) as AnalysisRunSummary["status"][])
    .map((status) => ({ status, value: counts[status] }))
    .filter((item) => item.value > 0);

  const total = data.reduce((sum, item) => sum + item.value, 0);

  if (total === 0) {
    return null;
  }

  return (
    <div className="chart-panel">
      <ResponsiveContainer height="100%" width="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            innerRadius="60%"
            isAnimationActive={!reduceMotion}
            nameKey="status"
            outerRadius="85%"
            paddingAngle={2}
          >
            {data.map((item) => (
              <Cell fill={STATUS_COLOR[item.status]} key={item.status} stroke="none" />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: chartColors.panel,
              border: `1px solid ${chartColors.border}`,
              borderRadius: 8,
              color: chartColors.text
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
