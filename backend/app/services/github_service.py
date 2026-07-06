from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.schemas.github import (
    ChangedFileSnapshot,
    GitHubPullRequestRead,
    GitHubPullRequestWithReviewState,
    PullRequestContextRead,
    PullRequestSnapshot,
)
from app.services import (
    github_app_auth_service,
    github_installation_service,
    pull_request_review_service,
)
from app.services.repository_service import get_repository

MAX_DIFF_BYTES = 5 * 1024 * 1024


class GitHubClient:
    base_url = "https://api.github.com"

    def __init__(self, token: str | None = None) -> None:
        self.token = token

    def _headers(self) -> dict[str, str]:
        if not self.token:
            raise AppError(
                503,
                "github_token_missing",
                "GitHub token is not configured.",
            )
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_repository(self, owner: str, name: str) -> dict[str, Any]:
        response = httpx.get(
            f"{self.base_url}/repos/{owner}/{name}",
            headers=self._headers(),
            timeout=20,
        )
        self._raise_for_response(response, owner, name)
        return response.json()

    def list_pull_requests(self, owner: str, name: str) -> list[GitHubPullRequestRead]:
        response = httpx.get(
            f"{self.base_url}/repos/{owner}/{name}/pulls",
            headers=self._headers(),
            params={"state": "open", "per_page": 50},
            timeout=20,
        )
        self._raise_for_response(response, owner, name)
        return [_map_pull_request(item) for item in response.json()]

    def get_pull_request(self, owner: str, name: str, pr_number: int) -> dict[str, Any]:
        response = httpx.get(
            f"{self.base_url}/repos/{owner}/{name}/pulls/{pr_number}",
            headers=self._headers(),
            timeout=20,
        )
        self._raise_for_response(response, owner, name)
        return response.json()

    def list_pull_request_files(
        self, owner: str, name: str, pr_number: int
    ) -> list[ChangedFileSnapshot]:
        files: list[ChangedFileSnapshot] = []
        page = 1
        per_page = 100
        while True:
            response = httpx.get(
                f"{self.base_url}/repos/{owner}/{name}/pulls/{pr_number}/files",
                headers=self._headers(),
                params={"per_page": per_page, "page": page},
                timeout=20,
            )
            self._raise_for_response(response, owner, name)
            items = response.json()
            files.extend(_map_changed_file(item) for item in items)
            if len(items) < per_page:
                break
            page += 1
        return files

    def get_pull_request_diff(
        self, owner: str, name: str, pr_number: int
    ) -> tuple[str, bool]:
        headers = self._headers()
        headers["Accept"] = "application/vnd.github.v3.diff"
        response = httpx.get(
            f"{self.base_url}/repos/{owner}/{name}/pulls/{pr_number}",
            headers=headers,
            timeout=20,
        )
        self._raise_for_response(response, owner, name)
        content = response.content
        truncated = len(content) > MAX_DIFF_BYTES
        diff = content[:MAX_DIFF_BYTES].decode("utf-8", errors="replace")
        return diff, truncated

    def list_issue_comments(
        self, owner: str, name: str, pr_number: int
    ) -> list[dict[str, Any]]:
        response = httpx.get(
            f"{self.base_url}/repos/{owner}/{name}/issues/{pr_number}/comments",
            headers=self._headers(),
            params={"per_page": 100},
            timeout=20,
        )
        self._raise_for_response(response, owner, name)
        return response.json()

    def create_issue_comment(
        self, owner: str, name: str, pr_number: int, body: str
    ) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/repos/{owner}/{name}/issues/{pr_number}/comments",
            headers=self._headers(),
            json={"body": body},
            timeout=20,
        )
        self._raise_for_response(response, owner, name)
        return response.json()

    def update_issue_comment(
        self, owner: str, name: str, comment_id: int, body: str
    ) -> dict[str, Any]:
        response = httpx.patch(
            f"{self.base_url}/repos/{owner}/{name}/issues/comments/{comment_id}",
            headers=self._headers(),
            json={"body": body},
            timeout=20,
        )
        self._raise_for_response(response, owner, name)
        return response.json()

    def create_commit_status(
        self,
        owner: str,
        name: str,
        sha: str,
        state: str,
        context: str,
        description: str,
    ) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/repos/{owner}/{name}/statuses/{sha}",
            headers=self._headers(),
            json={
                "state": state,
                "context": context,
                "description": description,
            },
            timeout=20,
        )
        self._raise_for_response(response, owner, name)
        return response.json()

    def get_pull_request_context(
        self, owner: str, name: str, pr_number: int
    ) -> PullRequestContextRead:
        pull_request = self.get_pull_request(owner, name, pr_number)
        changed_files = self.list_pull_request_files(owner, name, pr_number)
        diff_snapshot, diff_truncated = self.get_pull_request_diff(
            owner, name, pr_number
        )
        return PullRequestContextRead(
            pull_request=_map_pull_request_snapshot(pull_request),
            changed_files=changed_files,
            diff_snapshot=diff_snapshot,
            diff_truncated=diff_truncated,
        )

    def _raise_for_response(self, response: httpx.Response, owner: str, name: str) -> None:
        if response.status_code in {401, 403}:
            if response.headers.get("x-ratelimit-remaining") == "0":
                raise AppError(
                    429,
                    "github_rate_limited",
                    "GitHub API rate limit was reached. Try again later.",
                )
            raise AppError(
                403,
                "github_token_forbidden",
                "GitHub token is invalid or does not have permission.",
            )
        if response.status_code == 404:
            raise AppError(
                404,
                "github_repository_not_found",
                f"Repository {owner}/{name} was not found or the token does not have access.",
            )
        if response.is_error:
            raise AppError(
                502,
                "github_request_failed",
                "GitHub API request failed.",
            )


def installation_client_for_repository(
    db: Session,
    repository_id,
) -> GitHubClient:
    installation_link = (
        github_installation_service.get_active_installation_for_repository(
            db,
            repository_id,
        )
    )
    token = github_app_auth_service.generate_installation_token(
        installation_link.installation.installation_id
    )
    return GitHubClient(token)


def list_repository_pull_requests(
    db: Session, repository_id
) -> list[GitHubPullRequestWithReviewState]:
    repository = get_repository(db, repository_id)
    if repository.github_repo_id is None:
        return []

    pull_requests = installation_client_for_repository(
        db,
        repository_id,
    ).list_pull_requests(
        repository.owner, repository.name
    )
    review_states = pull_request_review_service.get_pull_request_review_states(
        db, repository.id, pull_requests
    )
    return [
        GitHubPullRequestWithReviewState(
            **pull_request.model_dump(),
            review_state=review_states[pull_request.number],
        )
        for pull_request in pull_requests
    ]


def get_repository_pull_request_context(db: Session, repository_id, pr_number: int):
    repository = get_repository(db, repository_id)
    return installation_client_for_repository(
        db,
        repository_id,
    ).get_pull_request_context(
        repository.owner, repository.name, pr_number
    )


def _map_pull_request(item: dict[str, Any]) -> GitHubPullRequestRead:
    return GitHubPullRequestRead(
        number=item["number"],
        title=item["title"],
        user_login=item["user"]["login"],
        state=item["state"],
        draft=item["draft"],
        head_ref=item["head"]["ref"],
        head_sha=item["head"]["sha"],
        base_ref=item["base"]["ref"],
        html_url=item["html_url"],
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


def _map_pull_request_snapshot(item: dict[str, Any]) -> PullRequestSnapshot:
    return PullRequestSnapshot(
        number=item["number"],
        title=item["title"],
        body=item.get("body"),
        state=item["state"],
        draft=item["draft"],
        author_login=item["user"]["login"],
        html_url=item["html_url"],
        base_ref=item["base"]["ref"],
        head_ref=item["head"]["ref"],
        head_sha=item["head"]["sha"],
        base_sha=item.get("base", {}).get("sha"),
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


def _map_changed_file(item: dict[str, Any]) -> ChangedFileSnapshot:
    return ChangedFileSnapshot(
        filename=item["filename"],
        status=item["status"],
        additions=item["additions"],
        deletions=item["deletions"],
        changes=item["changes"],
        patch=item.get("patch"),
    )
