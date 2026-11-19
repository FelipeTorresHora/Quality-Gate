import logging
import os
from typing import Any
from uuid import UUID

from pydantic import ValidationError
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
from app.services.agent.schemas import (
    AIReviewGenerated,
    AIReviewPartial,
    InlineComment,
    parse_ai_review_snapshot,
)
from app.services.evidence_redaction_service import redact_text
from app.services.github_service import GitHubClient
from app.services.report_service import build_github_comment_body, github_comment_marker

log = logging.getLogger(__name__)


def publication_frontend_origin() -> str:
    settings = get_settings()
    production_host = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
    if os.environ.get("VERCEL") and production_host:
        host = production_host.strip().strip("/")
        if host.startswith("http://") or host.startswith("https://"):
            return host.rstrip("/")
        return f"https://{host}"
    return settings.frontend_origin.rstrip("/")


def analysis_run_target_url(analysis_run_id: UUID) -> str:
    origin = publication_frontend_origin().rstrip("/")
    return f"{origin}/analysis-runs/{analysis_run_id}"


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

    client = _client_for_run(db, run)

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


def publish_pending_commit_status(
    db: Session, analysis_run_id: UUID
) -> GitHubPublicationStatusResult:
    run = _get_run(db, analysis_run_id)
    config = run.repository.quality_gate_config
    if not config.publish_github_status:
        return GitHubPublicationStatusResult(
            enabled=False,
            published=False,
            skipped_reason="status_disabled",
        )
    if run.status != AnalysisRunStatus.RUNNING:
        return GitHubPublicationStatusResult(
            enabled=True,
            published=False,
            skipped_reason="run_not_running",
        )

    client = _client_for_run(db, run)
    return _publish_commit_status(client, run)


def try_publish_pending_commit_status(db: Session, analysis_run_id: UUID) -> None:
    try:
        publish_pending_commit_status(db, analysis_run_id)
    except Exception:
        log.exception(
            "GitHub pending status publication failed for analysis run %s",
            analysis_run_id,
        )


def try_publish_analysis_run_to_github(db: Session, analysis_run_id: UUID) -> None:
    try:
        publish_analysis_run_to_github(db, analysis_run_id)
    except Exception:
        log.exception(
            "GitHub publication failed for analysis run %s",
            analysis_run_id,
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


def _client_for_run(db: Session, run: AnalysisRun) -> GitHubClient:
    installation_link = (
        github_installation_service.get_active_installation_for_repository(
            db,
            run.repository_id,
        )
    )
    return GitHubClient(
        github_app_auth_service.generate_installation_token(
            installation_link.installation.installation_id
        )
    )


def _publish_comment(
    client: GitHubClient, run: AnalysisRun
) -> GitHubPublicationCommentResult:
    # COMMENT reviews are notes on the diff. They do not approve the Pull
    # Request or change Gate Decision (ADR 0032). Publication stays an explicit
    # action (ADR 0034).
    comments = _validated_inline_comments(run)
    if comments:
        try:
            published = client.create_pull_request_review(
                run.repository.owner,
                run.repository.name,
                run.pr_number,
                run.head_sha,
                build_github_comment_body(run),
                [_review_comment_payload(comment) for comment in comments],
            )
        except AppError as exc:
            # GitHub returns 422 when a comment line is outside the diff.
            # Fall back to the issue comment so the idempotency marker remains.
            if exc.status_code != 422:
                raise
        else:
            return GitHubPublicationCommentResult(
                enabled=True,
                published=True,
                html_url=published.get("html_url"),
                skipped_reason=None,
            )
    return _publish_issue_comment(client, run)


def _publish_issue_comment(
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
    target_url = analysis_run_target_url(run.id)
    client.create_commit_status(
        run.repository.owner,
        run.repository.name,
        run.head_sha,
        state,
        get_settings().github_status_context,
        description,
        target_url,
    )
    return GitHubPublicationStatusResult(
        enabled=True,
        published=True,
        target_sha=run.head_sha,
        state=state,
        target_url=target_url,
        skipped_reason=None,
    )


def _validated_inline_comments(run: AnalysisRun) -> list[InlineComment]:
    try:
        snapshot = parse_ai_review_snapshot(run.ai_review_json or {})
    except ValidationError:
        return []
    if not isinstance(snapshot, (AIReviewGenerated, AIReviewPartial)):
        return []
    return list(snapshot.inline_comments)


def _review_comment_payload(comment: InlineComment) -> dict[str, Any]:
    lines = [
        f"**{comment.title}** ({comment.severity.value})",
        "",
        comment.body,
    ]
    if comment.suggestion_code:
        lines.extend(["", "```suggestion", comment.suggestion_code, "```"])
    return {
        "path": comment.file_path,
        "line": comment.line_number,
        "body": redact_text("\n".join(lines)),
    }


def _status_state_and_description(run: AnalysisRun) -> tuple[str, str]:
    if run.status == AnalysisRunStatus.RUNNING:
        return "pending", "Quality gate running."
    if run.status == AnalysisRunStatus.ERROR:
        return "error", "Quality gate could not complete."
    if run.decision == GateDecision.PASS:
        return "success", "Quality gate passed."
    return "failure", "Quality gate failed."
