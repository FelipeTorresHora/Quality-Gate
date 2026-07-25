import type { DashboardRecentAnalysisRun, DashboardSummary } from "../types/api";

export type AlertSeverity = "error" | "warning";

export type DashboardAlert = {
  id: string;
  severity: AlertSeverity;
  title: string;
  detail: string;
};

export type InsightTone = "pass" | "fail" | "neutral" | "accent";

export type DashboardInsight = {
  id: string;
  label: string;
  value: string;
  hint?: string;
  tone?: InsightTone;
};

function sortRunsByRecency(
  runs: DashboardRecentAnalysisRun[]
): DashboardRecentAnalysisRun[] {
  return [...runs].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
}

export function deriveAlerts(summary: DashboardSummary): DashboardAlert[] {
  const alerts: DashboardAlert[] = [];

  if (summary.approval_rate !== null && summary.approval_rate < 70) {
    alerts.push({
      id: "low-approval-rate",
      severity: "warning",
      title: "Approval rate below target",
      detail: `${summary.approval_rate}% of analyzed Pull Requests are passing the quality gate — below the 70% healthy threshold.`
    });
  }

  const errorCount = summary.run_status_counts.error ?? 0;
  if (errorCount > 0) {
    alerts.push({
      id: "run-errors",
      severity: "error",
      title: `${errorCount} analysis run${errorCount === 1 ? "" : "s"} errored`,
      detail: "These runs failed to execute and did not produce a gate decision. Check the run detail for the failure reason."
    });
  }

  const severeFindings = summary.finding_counts
    .filter((item) => item.severity === "critical" || item.severity === "high")
    .reduce((total, item) => total + item.count, 0);
  if (severeFindings > 0) {
    alerts.push({
      id: "severe-findings",
      severity: "warning",
      title: `${severeFindings} critical or high severity finding${severeFindings === 1 ? "" : "s"}`,
      detail: "Findings at this severity are the most likely to block a gate. Review them from the affected Pull Requests."
    });
  }

  const decided = sortRunsByRecency(summary.recent_analysis_runs).filter(
    (run) => run.decision !== null
  );
  const streak = decided.slice(0, 3);
  if (streak.length === 3 && streak.every((run) => run.decision === "fail")) {
    alerts.push({
      id: "fail-streak",
      severity: "error",
      title: "3 consecutive failing gates",
      detail: "The most recent decided runs all failed the quality gate. This may indicate a systemic issue rather than isolated Pull Request problems."
    });
  }

  return alerts;
}

export function deriveInsights(summary: DashboardSummary): DashboardInsight[] {
  const insights: DashboardInsight[] = [];

  const [topBlocking] = summary.top_blocking_categories;
  if (topBlocking) {
    const totalBlocking = summary.top_blocking_categories.reduce(
      (total, item) => total + item.count,
      0
    );
    const share = totalBlocking > 0 ? Math.round((topBlocking.count / totalBlocking) * 100) : 0;
    insights.push({
      id: "top-blocking-category",
      label: "Top blocking category",
      value: topBlocking.category.replace("_", " "),
      hint: `${share}% of blocking findings`,
      tone: "fail"
    });
  }

  const passCount = summary.gate_decision_counts.pass ?? 0;
  const failCount = summary.gate_decision_counts.fail ?? 0;
  const decidedTotal = passCount + failCount;
  insights.push({
    id: "pass-fail-split",
    label: "Pass / fail split",
    value: decidedTotal === 0 ? "—" : `${passCount} / ${failCount}`,
    hint: decidedTotal === 0 ? "No decided runs yet" : `${decidedTotal} decided runs`,
    tone: decidedTotal === 0 ? "neutral" : failCount > passCount ? "fail" : "pass"
  });

  const repoCounts = new Map<string, number>();
  for (const run of summary.recent_analysis_runs) {
    repoCounts.set(run.repository_full_name, (repoCounts.get(run.repository_full_name) ?? 0) + 1);
  }
  const busiest = [...repoCounts.entries()].sort((a, b) => b[1] - a[1])[0];
  insights.push({
    id: "busiest-repo",
    label: "Busiest repository",
    value: busiest ? busiest[0] : "—",
    hint: busiest ? `${busiest[1]} recent run${busiest[1] === 1 ? "" : "s"}` : "No recent runs",
    tone: "accent"
  });

  const scoredRuns = summary.recent_analysis_runs.filter(
    (run): run is DashboardRecentAnalysisRun & { score: number } =>
      run.status === "completed" && run.score !== null
  );
  const avgScore =
    scoredRuns.length > 0
      ? scoredRuns.reduce((total, run) => total + run.score, 0) / scoredRuns.length
      : null;
  insights.push({
    id: "avg-score",
    label: "Avg. recent score",
    value: avgScore === null ? "—" : avgScore.toFixed(1),
    hint: avgScore === null ? "No completed runs yet" : `Across ${scoredRuns.length} completed runs`,
    tone: avgScore === null ? "neutral" : avgScore >= 70 ? "pass" : "fail"
  });

  const decided = sortRunsByRecency(summary.recent_analysis_runs).filter(
    (run) => run.decision !== null
  );
  if (decided.length >= 4) {
    const mid = Math.floor(decided.length / 2);
    const newerHalf = decided.slice(0, mid);
    const olderHalf = decided.slice(mid);
    const passRate = (runs: DashboardRecentAnalysisRun[]) =>
      runs.length === 0 ? 0 : runs.filter((run) => run.decision === "pass").length / runs.length;
    const newerRate = passRate(newerHalf);
    const olderRate = passRate(olderHalf);
    const delta = newerRate - olderRate;
    const trend = delta > 0.05 ? "Improving" : delta < -0.05 ? "Declining" : "Steady";
    insights.push({
      id: "trend",
      label: "Gate trend",
      value: trend,
      hint: "Newer runs vs. older runs in the recent window",
      tone: trend === "Improving" ? "pass" : trend === "Declining" ? "fail" : "neutral"
    });
  }

  return insights;
}
