from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analysis_finding import AnalysisFinding
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, GateDecision
from app.models.github_app_installation import GitHubAppInstallation
from app.models.quality_gate_config import QualityGateConfig
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.schemas.dashboard import (
    DashboardBlockingCategory,
    DashboardFindingCount,
    DashboardOpenPullRequestAction,
    DashboardOpenPullRequestActionKind,
    DashboardRecentAnalysisRun,
    DashboardReviewState,
    DashboardSummaryRead,
)
from app.schemas.github import GitHubPullRequestRead
from app.services import github_service

RECENT_RUN_LIMIT = 8
TOP_BLOCKING_CATEGORY_LIMIT = 5
OPEN_PR_ACTION_WINDOW = timedelta(days=14)
_ACTION_SORT_ORDER = {
    "error": 0,
    "fail": 1,
    "publication_off": 2,
    "outdated": 3,
}


def get_dashboard_summary(db: Session, user: User) -> DashboardSummaryRead:
    accessible_repository_ids = (
        select(UserRepositoryAccess.repository_id)
        .join(
            GitHubAppInstallation,
            GitHubAppInstallation.id == UserRepositoryAccess.installation_id,
        )
        .where(
            UserRepositoryAccess.user_id == user.id,
            GitHubAppInstallation.active.is_(True),
            GitHubAppInstallation.suspended_at.is_(None),
        )
    )
    total_repositories = (
        db.scalar(
            select(func.count(Repository.id)).where(
                Repository.id.in_(accessible_repository_ids)
            )
        )
        or 0
    )
    total_analysis_runs = (
        db.scalar(
            select(func.count(AnalysisRun.id)).where(
                AnalysisRun.repository_id.in_(accessible_repository_ids)
            )
        )
        or 0
    )

    run_status_counts = {status.value: 0 for status in AnalysisRunStatus}
    for status, count in db.execute(
        select(AnalysisRun.status, func.count(AnalysisRun.id)).group_by(
            AnalysisRun.status
        )
        .where(AnalysisRun.repository_id.in_(accessible_repository_ids))
    ):
        run_status_counts[_enum_value(status)] = count

    gate_decision_counts = {decision.value: 0 for decision in GateDecision}
    for decision, count in db.execute(
        select(AnalysisRun.decision, func.count(AnalysisRun.id))
        .where(
            AnalysisRun.repository_id.in_(accessible_repository_ids),
            AnalysisRun.decision.is_not(None),
        )
        .group_by(AnalysisRun.decision)
    ):
        gate_decision_counts[_enum_value(decision)] = count

    approval_rate = _calculate_approval_rate(db, accessible_repository_ids)

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
            .where(AnalysisRun.repository_id.in_(accessible_repository_ids))
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
            .join(AnalysisRun, AnalysisFinding.analysis_run_id == AnalysisRun.id)
            .where(AnalysisRun.repository_id.in_(accessible_repository_ids))
            .group_by(AnalysisFinding.category, AnalysisFinding.severity)
            .order_by(AnalysisFinding.category, AnalysisFinding.severity)
        )
    ]

    top_blocking_categories = [
        DashboardBlockingCategory(category=category, count=count)
        for category, count in db.execute(
            select(AnalysisFinding.category, func.count(AnalysisFinding.id))
            .join(AnalysisRun, AnalysisFinding.analysis_run_id == AnalysisRun.id)
            .where(
                AnalysisRun.repository_id.in_(accessible_repository_ids),
                AnalysisFinding.blocking.is_(True),
            )
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
        open_pull_requests_needing_action=_open_pull_requests_needing_action(
            db, accessible_repository_ids
        ),
    )


def _open_pull_requests_needing_action(
    db: Session, accessible_repository_ids
) -> list[DashboardOpenPullRequestAction]:
    latest_runs = _latest_candidate_runs(db, accessible_repository_ids)
    if not latest_runs:
        return []

    repository_ids = {run.repository_id for run in latest_runs}
    repositories = {
        repository.id: repository
        for repository in db.scalars(
            select(Repository).where(Repository.id.in_(repository_ids))
        )
    }
    publication_flags = _publication_flags_by_repository(db, repository_ids)
    open_pull_requests = _open_pull_requests_by_repository(db, repository_ids)

    items: list[DashboardOpenPullRequestAction] = []
    for run in latest_runs:
        live_pull_request = open_pull_requests.get(run.repository_id, {}).get(
            run.pr_number
        )
        if live_pull_request is None:
            continue
        repository = repositories[run.repository_id]
        comment_on_github, publish_github_status = publication_flags.get(
            run.repository_id, (False, False)
        )
        review_state = _review_state(run, live_pull_request)
        action = _action_for_open_pull_request(
            run,
            review_state,
            comment_on_github=comment_on_github,
            publish_github_status=publish_github_status,
        )
        if action is None:
            continue
        items.append(
            DashboardOpenPullRequestAction(
                repository_id=run.repository_id,
                repository_full_name=repository.full_name,
                pr_number=run.pr_number,
                pr_title=live_pull_request.title,
                html_url=live_pull_request.html_url
                or _snapshot_html_url(run.pull_request_snapshot_json),
                head_sha=live_pull_request.head_sha,
                analysis_run_id=run.id,
                status=run.status,
                decision=run.decision,
                review_state=review_state,
                action=action,
                comment_on_github=comment_on_github,
                publish_github_status=publish_github_status,
                created_at=run.created_at,
            )
        )

    items.sort(
        key=lambda item: (
            _ACTION_SORT_ORDER.get(item.action, 9),
            -item.created_at.timestamp(),
            item.repository_full_name,
            item.pr_number,
        )
    )
    return items


def _latest_candidate_runs(
    db: Session, accessible_repository_ids
) -> list[AnalysisRun]:
    cutoff = datetime.now(UTC) - OPEN_PR_ACTION_WINDOW
    latest_runs = list(
        db.scalars(
            select(AnalysisRun)
            .where(
                AnalysisRun.repository_id.in_(accessible_repository_ids),
                AnalysisRun.created_at >= cutoff,
            )
            .distinct(AnalysisRun.repository_id, AnalysisRun.pr_number)
            .order_by(
                AnalysisRun.repository_id,
                AnalysisRun.pr_number,
                AnalysisRun.created_at.desc(),
                AnalysisRun.id.desc(),
            )
        )
    )
    return [
        run
        for run in latest_runs
        if run.status in (AnalysisRunStatus.COMPLETED, AnalysisRunStatus.ERROR)
    ]


def _publication_flags_by_repository(
    db: Session, repository_ids: set[UUID]
) -> dict[UUID, tuple[bool, bool]]:
    if not repository_ids:
        return {}
    return {
        config.repository_id: (
            config.comment_on_github,
            config.publish_github_status,
        )
        for config in db.scalars(
            select(QualityGateConfig).where(
                QualityGateConfig.repository_id.in_(repository_ids)
            )
        )
    }


def _open_pull_requests_by_repository(
    db: Session, repository_ids: set[UUID]
) -> dict[UUID, dict[int, GitHubPullRequestRead]]:
    open_by_repository: dict[UUID, dict[int, GitHubPullRequestRead]] = {}
    for repository_id in repository_ids:
        try:
            pull_requests = github_service.list_repository_pull_requests(
                db, repository_id
            )
        except Exception:
            continue
        open_by_repository[repository_id] = {
            pull_request.number: pull_request for pull_request in pull_requests
        }
    return open_by_repository


def _review_state(
    run: AnalysisRun, pull_request: GitHubPullRequestRead
) -> DashboardReviewState:
    return "current" if run.head_sha == pull_request.head_sha else "outdated"


def _action_for_open_pull_request(
    run: AnalysisRun,
    review_state: DashboardReviewState,
    *,
    comment_on_github: bool,
    publish_github_status: bool,
) -> DashboardOpenPullRequestActionKind | None:
    if review_state == "outdated":
        return "outdated"
    if run.status == AnalysisRunStatus.ERROR:
        return "error"
    if (
        run.status == AnalysisRunStatus.COMPLETED
        and run.decision == GateDecision.FAIL
    ):
        if not comment_on_github and not publish_github_status:
            return "publication_off"
        return "fail"
    return None


def _snapshot_html_url(snapshot: dict | None) -> str | None:
    if not isinstance(snapshot, dict):
        return None
    html_url = snapshot.get("html_url")
    return html_url if isinstance(html_url, str) else None


def _calculate_approval_rate(db: Session, accessible_repository_ids) -> float | None:
    decided_completed_count = (
        db.scalar(
            select(func.count(AnalysisRun.id)).where(
                AnalysisRun.repository_id.in_(accessible_repository_ids),
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
                AnalysisRun.repository_id.in_(accessible_repository_ids),
                AnalysisRun.status == AnalysisRunStatus.COMPLETED,
                AnalysisRun.decision == GateDecision.PASS,
            )
        )
        or 0
    )
    return round((passing_completed_count / decided_completed_count) * 100, 1)


def _enum_value(value):
    return value.value if hasattr(value, "value") else value
