from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.models.analysis_run import AnalysisRun
from app.models.enums import (
    AnalysisRunStatus,
    AnalysisTriggerSource,
)
from app.schemas.github import PullRequestContextRead
from app.services.repository_service import get_repository


ENRICHMENT_ERROR_MESSAGE = (
    "GitHub Pull Request context could not be captured. "
    "Check token permissions and try again with a new Pull Request event."
)


def list_analysis_runs(db: Session, repository_id: UUID) -> list[AnalysisRun]:
    get_repository(db, repository_id)
    return list(
        db.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.repository_id == repository_id)
            .order_by(AnalysisRun.created_at.desc())
        )
    )


def get_analysis_run(db: Session, analysis_run_id: UUID) -> AnalysisRun:
    run = db.scalar(
        select(AnalysisRun)
        .options(selectinload(AnalysisRun.findings))
        .where(AnalysisRun.id == analysis_run_id)
    )
    if run is None:
        raise AppError(404, "analysis_run_not_found", "Analysis run was not found.")
    return run


def get_analysis_run_by_pr_head(
    db: Session, repository_id: UUID, pr_number: int, head_sha: str
) -> AnalysisRun | None:
    return db.scalar(
        select(AnalysisRun).where(
            AnalysisRun.repository_id == repository_id,
            AnalysisRun.pr_number == pr_number,
            AnalysisRun.head_sha == head_sha,
        )
    )


def _build_pending_run(
    repository_id: UUID,
    context_model: PullRequestContextRead,
    trigger_source: AnalysisTriggerSource,
) -> AnalysisRun:
    return AnalysisRun(
        repository_id=repository_id,
        pr_number=context_model.pull_request.number,
        head_sha=context_model.pull_request.head_sha,
        status=AnalysisRunStatus.PENDING,
        decision=None,
        trigger_source=trigger_source,
        score=None,
        coverage_result_json={},
        security_result_json={},
        technical_debt_result_json={},
        ai_review_json={},
        pull_request_snapshot_json=context_model.pull_request.model_dump(mode="json"),
        changed_files_snapshot_json=[
            changed_file.model_dump(mode="json")
            for changed_file in context_model.changed_files
        ],
        diff_snapshot=context_model.diff_snapshot,
        diff_truncated=context_model.diff_truncated,
        final_report_markdown=None,
        error_message=None,
        started_at=None,
        finished_at=None,
    )


def _create_or_reuse(
    db: Session,
    repository_id: UUID,
    context_model: PullRequestContextRead,
    trigger_source: AnalysisTriggerSource,
) -> AnalysisRun:
    existing = get_analysis_run_by_pr_head(
        db,
        repository_id,
        context_model.pull_request.number,
        context_model.pull_request.head_sha,
    )
    if existing is not None:
        return get_analysis_run(db, existing.id)
    return _commit_new_run_or_reuse(
        db, _build_pending_run(repository_id, context_model, trigger_source)
    )


def create_or_reuse_webhook_analysis_run(
    db: Session, repository_id: UUID, context: PullRequestContextRead | dict
) -> AnalysisRun:
    return _create_or_reuse(
        db,
        repository_id,
        _coerce_context(context),
        AnalysisTriggerSource.GITHUB_WEBHOOK,
    )


def create_or_reuse_manual_analysis_run(
    db: Session,
    repository_id: UUID,
    context: PullRequestContextRead | dict,
) -> AnalysisRun:
    return _create_or_reuse(
        db,
        repository_id,
        _coerce_context(context),
        AnalysisTriggerSource.MANUAL,
    )


def create_or_reuse_error_webhook_analysis_run(
    db: Session,
    repository_id: UUID,
    pull_request_snapshot: dict,
    error_message: str = ENRICHMENT_ERROR_MESSAGE,
) -> AnalysisRun:
    pr_number = int(pull_request_snapshot["number"])
    head_sha = str(pull_request_snapshot["head_sha"])
    existing = get_analysis_run_by_pr_head(db, repository_id, pr_number, head_sha)
    if existing is not None:
        return get_analysis_run(db, existing.id)

    run = AnalysisRun(
        repository_id=repository_id,
        pr_number=pr_number,
        head_sha=head_sha,
        status=AnalysisRunStatus.ERROR,
        decision=None,
        trigger_source=AnalysisTriggerSource.GITHUB_WEBHOOK,
        score=None,
        coverage_result_json={},
        security_result_json={},
        technical_debt_result_json={},
        ai_review_json={},
        pull_request_snapshot_json=pull_request_snapshot,
        changed_files_snapshot_json=[],
        diff_snapshot=None,
        diff_truncated=False,
        final_report_markdown=None,
        error_message=error_message,
        started_at=None,
        finished_at=None,
    )
    return _commit_new_run_or_reuse(db, run)


def _coerce_context(context: PullRequestContextRead | dict) -> PullRequestContextRead:
    if isinstance(context, PullRequestContextRead):
        return context
    return PullRequestContextRead.model_validate(context)


def _commit_new_run_or_reuse(db: Session, run: AnalysisRun) -> AnalysisRun:
    db.add(run)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = get_analysis_run_by_pr_head(
            db, run.repository_id, run.pr_number, run.head_sha
        )
        if existing is None:
            raise
        return get_analysis_run(db, existing.id)
    return get_analysis_run(db, run.id)
