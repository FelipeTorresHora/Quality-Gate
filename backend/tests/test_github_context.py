def _pull_request_context():
    return {
        "pull_request": {
            "number": 42,
            "title": "Add billing webhook",
            "body": "Implements billing webhook handling.",
            "state": "open",
            "draft": False,
            "author_login": "octocat",
            "html_url": "https://github.com/horinha04/meu-projeto/pull/42",
            "base_ref": "main",
            "head_ref": "feature/billing-webhook",
            "head_sha": "abc123",
            "base_sha": "def456",
            "created_at": "2026-06-21T10:00:00Z",
            "updated_at": "2026-06-21T11:00:00Z",
        },
        "changed_files": [
            {
                "filename": "backend/app/api/billing.py",
                "status": "added",
                "additions": 30,
                "deletions": 0,
                "changes": 30,
                "patch": "@@ -0,0 +1,30 @@",
            },
            {
                "filename": "README.md",
                "status": "modified",
                "additions": 4,
                "deletions": 1,
                "changes": 5,
            },
        ],
        "diff_snapshot": "diff --git a/README.md b/README.md\n",
        "diff_truncated": False,
    }


def test_get_pull_request_context_maps_github_data_without_creating_run(
    client, repository, monkeypatch
):
    from app.services.github_service import GitHubClient

    calls = []

    def fake_context(self, owner, name, pr_number):
        calls.append((owner, name, pr_number))
        return _pull_request_context()

    monkeypatch.setattr(
        GitHubClient, "get_pull_request_context", fake_context, raising=False
    )

    response = client.get(
        f"/api/repositories/{repository['id']}/pull-requests/42/context"
    )

    assert response.status_code == 200
    context = response.json()
    assert calls == [("horinha04", "meu-projeto", 42)]
    assert context["pull_request"]["number"] == 42
    assert context["pull_request"]["author_login"] == "octocat"
    assert context["pull_request"]["head_sha"] == "abc123"
    assert context["changed_files"][0]["filename"] == "backend/app/api/billing.py"
    assert context["changed_files"][0]["patch"] == "@@ -0,0 +1,30 @@"
    assert context["changed_files"][1]["patch"] is None
    assert context["diff_snapshot"].startswith("diff --git")
    assert context["diff_truncated"] is False

    runs_response = client.get(f"/api/repositories/{repository['id']}/analysis-runs")
    assert runs_response.status_code == 200
    assert runs_response.json() == []
