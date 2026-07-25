import { Link } from "react-router-dom";

import type { AnalysisRunSummary } from "../types/api";

type RunTickerProps = {
  runs: AnalysisRunSummary[];
  getLabel?: (run: AnalysisRunSummary) => string;
  max?: number;
};

function tickClass(run: AnalysisRunSummary): string {
  if (run.status === "running") return "tick tick-running";
  if (run.decision === "pass") return "tick tick-pass";
  if (run.decision === "fail") return "tick tick-fail";
  return "tick tick-neutral";
}

function defaultLabel(run: AnalysisRunSummary): string {
  const decision = run.decision ?? run.status;
  const score = run.score === null ? "" : ` · score ${run.score}`;
  return `#${run.pr_number} · ${decision}${score}`;
}

export default function RunTicker({ runs, getLabel, max = 40 }: RunTickerProps) {
  const ordered = [...runs]
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .slice(-max);

  if (ordered.length === 0) {
    return null;
  }

  const label = getLabel ?? defaultLabel;

  return (
    <div aria-label="Recent run outcomes" className="run-ticker" role="list">
      {ordered.map((run) => (
        <Link
          aria-label={label(run)}
          className={tickClass(run)}
          data-tip={label(run)}
          key={run.id}
          role="listitem"
          to={`/analysis-runs/${run.id}`}
        />
      ))}
    </div>
  );
}
