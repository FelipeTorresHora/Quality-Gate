from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analysis_finding import AnalysisFinding
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, GateDecision
from app.models.repository import Repository
from app.schemas.dashboard import (
    DashboardBlockingCategory,
    DashboardFindingCount,
    DashboardRecentAnalysisRun,
    DashboardSummaryRead,
)

RECENT_RUN_LIMIT = 8
TOP_BLOCKING_CATEGORY_LIMIT = 5


def get_dashboard_summary(db: Session) -> DashboardSummaryRead:
    total_repositories = db.scalar(select(func.count(Repository.id))) or 0
    total_analysis_runs = db.scalar(select(func.count(AnalysisRun.id))) or 0

    run_status_counts = {status.value: 0 for status in AnalysisRunStatus}
    for status, count in db.execute(
        select(AnalysisRun.status, func.count(AnalysisRun.id)).group_by(
            AnalysisRun.status
        )
    ):
        run_status_counts[_enum_value(status)] = count

    gate_decision_counts = {decision.value: 0 for decision in GateDecision}
    for decision, count in db.execute(
        select(AnalysisRun.decision, func.count(AnalysisRun.id))
        .where(AnalysisRun.decision.is_not(None))
        .group_by(AnalysisRun.decision)
    ):
        gate_decision_counts[_enum_value(decision)] = count

    approval_rate = _calculate_approval_rate(db)

    recent_analysis_runs = [
        DashboardRecentAnalysisRun(
            id=run.id,
            repository_id=run.repository_id,
            repository_full_name=repository_full_name,
            pr_number=run.pr_number,
            head_sha=run.head_sha,
            status=run.status,
            decision=run.decision,
            trigger_source=run.trigger_source,
            score=run.score,
            created_at=run.created_at,
        )
        for run, repository_full_name in db.execute(
            select(AnalysisRun, Repository.full_name)
            .join(Repository, AnalysisRun.repository_id == Repository.id)
            .order_by(AnalysisRun.created_at.desc(), AnalysisRun.pr_number.desc())
            .limit(RECENT_RUN_LIMIT)
        )
    ]

    finding_counts = [
        DashboardFindingCount(
            category=category,
            severity=severity,
            count=count,
        )
        for category, severity, count in db.execute(
            select(
                AnalysisFinding.category,
                AnalysisFinding.severity,
                func.count(AnalysisFinding.id),
            )
            .group_by(AnalysisFinding.category, AnalysisFinding.severity)
            .order_by(AnalysisFinding.category, AnalysisFinding.severity)
        )
    ]

    top_blocking_categories = [
        DashboardBlockingCategory(category=category, count=count)
        for category, count in db.execute(
            select(AnalysisFinding.category, func.count(AnalysisFinding.id))
            .where(AnalysisFinding.blocking.is_(True))
            .group_by(AnalysisFinding.category)
            .order_by(func.count(AnalysisFinding.id).desc(), AnalysisFinding.category)
            .limit(TOP_BLOCKING_CATEGORY_LIMIT)
        )
    ]

    return DashboardSummaryRead(
        total_repositories=total_repositories,
        total_analysis_runs=total_analysis_runs,
        run_status_counts=run_status_counts,
        gate_decision_counts=gate_decision_counts,
        approval_rate=approval_rate,
        recent_analysis_runs=recent_analysis_runs,
        finding_counts=finding_counts,
        top_blocking_categories=top_blocking_categories,
    )


def _calculate_approval_rate(db: Session) -> float | None:
    decided_completed_count = (
        db.scalar(
            select(func.count(AnalysisRun.id)).where(
                AnalysisRun.status == AnalysisRunStatus.COMPLETED,
                AnalysisRun.decision.is_not(None),
            )
        )
        or 0
    )
    if decided_completed_count == 0:
        return None

    passing_completed_count = (
        db.scalar(
            select(func.count(AnalysisRun.id)).where(
                AnalysisRun.status == AnalysisRunStatus.COMPLETED,
                AnalysisRun.decision == GateDecision.PASS,
            )
        )
        or 0
    )
    return round((passing_completed_count / decided_completed_count) * 100, 1)


def _enum_value(value):
    return value.value if hasattr(value, "value") else value
