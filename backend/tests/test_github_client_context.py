import httpx

from app.services.github_service import GitHubClient, MAX_DIFF_BYTES
from app.services.runner_service import CommandResult, repository_clone_url


def _github_response(**kwargs):
    request = httpx.Request("GET", "https://api.github.com")
    return httpx.Response(request=request, **kwargs)


def test_github_client_uses_provided_installation_token(monkeypatch):
    seen_headers = []

    class FakeResponse:
        status_code = 200
        headers = {}

        def json(self):
            return []

        @property
        def is_error(self):
            return False

    def fake_get(url, headers, params=None, timeout=20):
        seen_headers.append(headers)
        return FakeResponse()

    monkeypatch.setattr(
        "app.services.github_service.httpx.get",
        fake_get,
    )

    client = GitHubClient("installation-token")
    client.list_pull_requests("octo-org", "quality-api")

    assert seen_headers[0]["Authorization"] == "Bearer installation-token"


def test_repository_clone_url_accepts_installation_token():
    url = repository_clone_url(
        "octo-org",
        "quality-api",
        "installation-token",
    )

    assert url == (
        "https://x-access-token:installation-token"
        "@github.com/octo-org/quality-api.git"
    )


def test_command_snapshot_redacts_clone_token():
    result = CommandResult(
        command=(
            "git clone https://x-access-token:installation-token"
            "@github.com/octo-org/quality-api.git repo"
        ),
        exit_code=0,
        stdout="",
        stderr="",
        duration_seconds=0.1,
    )

    assert result.to_snapshot()["command"] == (
        "git clone https://x-access-token:***"
        "@github.com/octo-org/quality-api.git repo"
    )


def test_pull_request_context_maps_paginated_files_and_truncates_large_diff(monkeypatch):
    first_page_files = [
        {
            "filename": f"src/file_{index}.py",
            "status": "modified",
            "additions": 1,
            "deletions": 0,
            "changes": 1,
            "patch": "@@ -1 +1 @@",
        }
        for index in range(100)
    ]
    second_page_files = [
        {
            "filename": "README.md",
            "status": "modified",
            "additions": 4,
            "deletions": 1,
            "changes": 5,
        }
    ]
    large_diff = b"a" * (MAX_DIFF_BYTES + 10)

    def fake_get(url, headers, params=None, timeout=20):
        if url.endswith("/pulls/42/files"):
            if params["page"] == 1:
                return _github_response(status_code=200, json=first_page_files)
            return _github_response(status_code=200, json=second_page_files)
        if url.endswith("/pulls/42") and headers["Accept"] == "application/vnd.github.v3.diff":
            return _github_response(status_code=200, content=large_diff)
        if url.endswith("/pulls/42"):
            return _github_response(
                status_code=200,
                json={
                    "number": 42,
                    "title": "Add billing webhook",
                    "body": "Implements billing webhook handling.",
                    "state": "open",
                    "draft": False,
                    "user": {"login": "octocat"},
                    "html_url": "https://github.com/horinha04/meu-projeto/pull/42",
                    "base": {"ref": "main", "sha": "base123"},
                    "head": {"ref": "feature/billing-webhook", "sha": "abc123"},
                    "created_at": "2026-06-21T10:00:00Z",
                    "updated_at": "2026-06-21T11:00:00Z",
                },
            )
        raise AssertionError(f"Unexpected GitHub URL: {url}")

    monkeypatch.setattr(httpx, "get", fake_get)

    context = GitHubClient("token").get_pull_request_context(
        "horinha04", "meu-projeto", 42
    )

    assert context.pull_request.number == 42
    assert context.pull_request.author_login == "octocat"
    assert len(context.changed_files) == 101
    assert context.changed_files[0].filename == "src/file_0.py"
    assert context.changed_files[-1].filename == "README.md"
    assert context.changed_files[-1].patch is None
    assert len(context.diff_snapshot.encode()) == MAX_DIFF_BYTES
    assert context.diff_truncated is True
