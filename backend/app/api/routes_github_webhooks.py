from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.github import GitHubWebhookResult
from app.services import github_webhook_service

router = APIRouter(tags=["github-webhooks"])


@router.post(
    "/api/github/webhooks",
    response_model=GitHubWebhookResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def receive_github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None, alias="X-GitHub-Event"),
    x_hub_signature_256: str | None = Header(
        default=None,
        alias="X-Hub-Signature-256",
    ),
    db: Session = Depends(get_db),
):
    body = await request.body()
    return github_webhook_service.process_github_webhook(
        db,
        body,
        x_github_event,
        x_hub_signature_256,
    )
