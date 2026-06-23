from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.analysis_run import AnalysisRun
from app.models.enums import AnalysisRunStatus, GateDecision
from app.models.repository import Repository
from app.schemas.analysis import (
    GitHubPublicationCommentResult,
    GitHubPublicationResult,
    GitHubPublicationStatusResult,
)
from app.services import github_app_auth_service, github_installation_service
from app.services.github_service import GitHubClient
from app.services.report_service import build_github_comment_body, github_comment_marker


def publish_analysis_run_to_github(
    db: Session, analysis_run_id: UUID
) -> GitHubPublicationResult:
    run = _get_run(db, analysis_run_id)
    if run.status not in {AnalysisRunStatus.COMPLETED, AnalysisRunStatus.ERROR}:
        raise AppError(
            409,
            "analysis_run_not_publishable",
            "Only completed or errored analysis runs can be published.",
        )

    config = run.repository.quality_gate_config
    if not config.comment_on_github and not config.publish_github_status:
        return GitHubPublicationResult(
            analysis_run_id=run.id,
            comment=GitHubPublicationCommentResult(
                enabled=False,
                published=False,
                skipped_reason="comment_disabled",
            ),
            commit_status=GitHubPublicationStatusResult(
                enabled=False,
                published=False,
                skipped_reason="status_disabled",
            ),
        )

    installation_link = (
        github_installation_service.get_active_installation_for_repository(
            db,
            run.repository_id,
        )
    )
    client = GitHubClient(
        github_app_auth_service.generate_installation_token(
            installation_link.installation.installation_id
        )
    )

    comment_result = (
        _publish_comment(client, run)
        if config.comment_on_github
        else GitHubPublicationCommentResult(
            enabled=False,
            published=False,
            skipped_reason="comment_disabled",
        )
    )
    status_result = (
        _publish_commit_status(client, run)
        if config.publish_github_status
        else GitHubPublicationStatusResult(
            enabled=False,
            published=False,
            skipped_reason="status_disabled",
        )
    )

    return GitHubPublicationResult(
        analysis_run_id=run.id,
        comment=comment_result,
        commit_status=status_result,
    )


def _get_run(db: Session, analysis_run_id: UUID) -> AnalysisRun:
    run = db.scalar(
        select(AnalysisRun)
        .options(
            selectinload(AnalysisRun.findings),
            selectinload(AnalysisRun.repository).selectinload(
                Repository.quality_gate_config
            ),
        )
        .where(AnalysisRun.id == analysis_run_id)
    )
    if run is None:
        raise AppError(404, "analysis_run_not_found", "Analysis run was not found.")
    return run


def _publish_comment(
    client: GitHubClient, run: AnalysisRun
) -> GitHubPublicationCommentResult:
    owner = run.repository.owner
    name = run.repository.name
    marker = github_comment_marker(run)
    body = build_github_comment_body(run)
    comments = client.list_issue_comments(owner, name, run.pr_number)
    existing = next(
        (
            comment
            for comment in comments
            if marker in str(comment.get("body") or "")
        ),
        None,
    )
    if existing:
        published = client.update_issue_comment(
            owner,
            name,
            int(existing["id"]),
            body,
        )
    else:
        published = client.create_issue_comment(owner, name, run.pr_number, body)
    return GitHubPublicationCommentResult(
        enabled=True,
        published=True,
        html_url=published.get("html_url"),
        skipped_reason=None,
    )


def _publish_commit_status(
    client: GitHubClient, run: AnalysisRun
) -> GitHubPublicationStatusResult:
    state, description = _status_state_and_description(run)
    client.create_commit_status(
        run.repository.owner,
        run.repository.name,
        run.head_sha,
        state,
        get_settings().github_status_context,
        description,
    )
    return GitHubPublicationStatusResult(
        enabled=True,
        published=True,
        target_sha=run.head_sha,
        state=state,
        skipped_reason=None,
    )


def _status_state_and_description(run: AnalysisRun) -> tuple[str, str]:
    if run.status == AnalysisRunStatus.ERROR:
        return "error", "Quality gate could not complete."
    if run.decision == GateDecision.PASS:
        return "success", "Quality gate passed."
    return "failure", "Quality gate failed."
