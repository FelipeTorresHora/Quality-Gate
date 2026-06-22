from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.github import (
    GitHubPullRequestWithReviewState,
    GitHubRepositoryCreate,
    PullRequestContextRead,
)
from app.schemas.repository import RepositoryCreate, RepositoryRead
from app.services import github_service, repository_service

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.get("", response_model=list[RepositoryRead])
def list_repositories(db: Session = Depends(get_db)):
    return repository_service.list_repositories(db)


@router.post("", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
def create_repository(payload: RepositoryCreate, db: Session = Depends(get_db)):
    return repository_service.create_repository(db, payload)


@router.post(
    "/github", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED
)
def create_repository_from_github(
    payload: GitHubRepositoryCreate, db: Session = Depends(get_db)
):
    return github_service.create_repository_from_github(db, payload.owner, payload.name)


@router.get("/{repository_id}", response_model=RepositoryRead)
def get_repository(repository_id: UUID, db: Session = Depends(get_db)):
    return repository_service.get_repository(db, repository_id)


@router.get(
    "/{repository_id}/pull-requests",
    response_model=list[GitHubPullRequestWithReviewState],
)
def list_pull_requests(repository_id: UUID, db: Session = Depends(get_db)):
    return github_service.list_repository_pull_requests(db, repository_id)


@router.get(
    "/{repository_id}/pull-requests/{pr_number}/context",
    response_model=PullRequestContextRead,
)
def get_pull_request_context(
    repository_id: UUID, pr_number: int, db: Session = Depends(get_db)
):
    return github_service.get_repository_pull_request_context(
        db, repository_id, pr_number
    )
