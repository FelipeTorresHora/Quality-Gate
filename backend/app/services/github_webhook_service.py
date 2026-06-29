import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.enums import AnalysisRunStatus
from app.models.user import User
from app.schemas.github import GitHubWebhookResult, PullRequestContextRead
from app.services import (
    analysis_execution_service,
    analysis_service,
    github_installation_service,
    github_service,
)
from app.services.repository_service import get_repository_by_full_name

SUPPORTED_PULL_REQUEST_ACTIONS = {
    "opened",
    "reopened",
    "synchronize",
    "ready_for_review",
}


def process_github_webhook(
    db: Session,
    body: bytes,
    event: str | None,
    signature_header: str | None,
    background_tasks: BackgroundTasks | None = None,
) -> GitHubWebhookResult:
    settings = get_settings()
    secret = settings.github_webhook_secret
    if not secret:
        raise AppError(
            503,
            "github_webhook_secret_missing",
            "GitHub webhook secret is not configured.",
        )
    if not _has_valid_signature(body, secret, signature_header):
        raise AppError(
            401,
            "github_webhook_signature_invalid",
            "GitHub webhook signature is invalid.",
        )
    payload = _parse_payload(body)
    if event in {"installation", "installation_repositories"}:
        _process_installation_event(db, event, payload)
        return _ignored("installation_synced")
    if event != "pull_request":
        return _ignored("unsupported_event")

    action = payload.get("action")
    pull_request = payload.get("pull_request") or {}
    if action == "closed" or pull_request.get("state") == "closed":
        return _ignored("closed_pull_request")
    if action not in SUPPORTED_PULL_REQUEST_ACTIONS:
        return _ignored("unsupported_action")
    if pull_request.get("draft") is True and action != "ready_for_review":
        return _ignored("draft_pull_request")

    repository_payload = payload.get("repository") or {}
    repository_full_name = repository_payload.get("full_name")
    if not repository_full_name:
        return _ignored("unknown_repository")
    repository = get_repository_by_full_name(db, repository_full_name)
    if repository is None:
        return _ignored("unknown_repository")

    fallback_snapshot = _pull_request_snapshot_from_payload(pull_request)
    created_new = False
    try:
        context = github_service.installation_client_for_repository(
            db,
            repository.id,
        ).get_pull_request_context(
            repository.owner,
            repository.name,
            int(fallback_snapshot["number"]),
        )
        context_model = PullRequestContextRead.model_validate(context)
        existing = analysis_service.get_analysis_run_by_pr_head(
            db,
            repository.id,
            context_model.pull_request.number,
            context_model.pull_request.head_sha,
        )
        run = analysis_service.create_or_reuse_webhook_analysis_run(
            db,
            repository.id,
            context_model,
        )
        created_new = existing is None and run.status == AnalysisRunStatus.PENDING
    except Exception:
        run = analysis_service.create_or_reuse_error_webhook_analysis_run(
            db,
            repository.id,
            fallback_snapshot,
        )

    if created_new:
        if background_tasks is not None:
            background_tasks.add_task(_execute_run_by_id, run.id)
        else:
            analysis_execution_service.execute_analysis_run(db, run.id)

    return GitHubWebhookResult(
        ignored=False,
        reason=None,
        analysis_run_id=run.id,
    )


def _process_installation_event(
    db: Session,
    event: str,
    payload: dict[str, Any],
) -> None:
    action = payload.get("action")
    installation_payload = payload.get("installation") or {}
    installation_id = installation_payload.get("id")
    if installation_id is None:
        return

    if event == "installation":
        if action in {"deleted", "suspend"}:
            github_installation_service.deactivate_installation(
                db,
                int(installation_id),
                suspended_at=datetime.now(UTC) if action == "suspend" else None,
                purge=action == "deleted",
            )
            return
        if action in {"created", "new_permissions_accepted", "unsuspend"}:
            github_installation_service.sync_installation_payload(
                db,
                user=_find_webhook_user(db, payload),
                installation_payload=installation_payload,
                repositories_payload=payload.get("repositories") or [],
                replace_repositories=action == "created",
            )
        return

    if event == "installation_repositories":
        added = payload.get("repositories_added") or []
        if added:
            github_installation_service.sync_installation_payload(
                db,
                user=_find_webhook_user(db, payload),
                installation_payload=installation_payload,
                repositories_payload=added,
                replace_repositories=False,
            )
        removed_ids = {
            int(repository["id"])
            for repository in payload.get("repositories_removed") or []
        }
        github_installation_service.remove_installation_repositories(
            db,
            int(installation_id),
            removed_ids,
        )


def _find_webhook_user(db: Session, payload: dict[str, Any]) -> User | None:
    sender = payload.get("sender") or {}
    sender_id = sender.get("id")
    if sender_id is None:
        return None
    return db.scalar(
        select(User).where(User.github_user_id == int(sender_id))
    )


def _execute_run_by_id(analysis_run_id):
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        analysis_execution_service.execute_analysis_run(db, analysis_run_id)
    finally:
        db.close()


def _has_valid_signature(
    body: bytes, secret: str, signature_header: str | None
) -> bool:
    if not signature_header:
        return False
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    return hmac.compare_digest(expected, signature_header)


def _parse_payload(body: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AppError(
            400,
            "github_webhook_payload_invalid",
            "GitHub webhook payload is invalid.",
        ) from exc
    if not isinstance(parsed, dict):
        raise AppError(
            400,
            "github_webhook_payload_invalid",
            "GitHub webhook payload is invalid.",
        )
    return parsed


def _pull_request_snapshot_from_payload(pull_request: dict[str, Any]) -> dict[str, Any]:
    base = pull_request.get("base") or {}
    head = pull_request.get("head") or {}
    user = pull_request.get("user") or {}
    return {
        "number": pull_request["number"],
        "title": pull_request.get("title") or "",
        "body": pull_request.get("body"),
        "state": pull_request.get("state") or "",
        "draft": bool(pull_request.get("draft")),
        "author_login": user.get("login") or "",
        "html_url": pull_request.get("html_url") or "",
        "base_ref": base.get("ref") or "",
        "head_ref": head.get("ref") or "",
        "head_sha": head["sha"],
        "base_sha": base.get("sha"),
        "created_at": pull_request.get("created_at"),
        "updated_at": pull_request.get("updated_at"),
    }


def _ignored(reason: str) -> GitHubWebhookResult:
    return GitHubWebhookResult(ignored=True, reason=reason, analysis_run_id=None)
