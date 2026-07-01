from uuid import uuid4

from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource
from app.schemas.github import PullRequestContextRead
from app.services.analysis_service import _build_pending_run


def _context():
    return PullRequestContextRead.model_validate(
        {
            "pull_request": {
                "number": 5,
                "title": "Add feature",
                "body": None,
                "state": "open",
                "draft": False,
                "author_login": "octocat",
                "html_url": "https://github.com/octo/repo/pull/5",
                "base_ref": "main",
                "head_ref": "feature",
                "head_sha": "h5",
                "base_sha": "b5",
                "created_at": "2026-06-30T00:00:00Z",
                "updated_at": "2026-06-30T00:00:00Z",
            },
            "changed_files": [
                {
                    "filename": "a.py",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 0,
                    "changes": 1,
                    "patch": "+x",
                }
            ],
            "diff_snapshot": "diff --git a/a.py b/a.py",
            "diff_truncated": False,
        }
    )


def test_build_pending_run_sets_trigger_source_and_defaults():
    context = _context()
    repository_id = uuid4()

    run = _build_pending_run(repository_id, context, AnalysisTriggerSource.MANUAL)

    assert run.repository_id == repository_id
    assert run.trigger_source == AnalysisTriggerSource.MANUAL
    assert run.status == AnalysisRunStatus.PENDING
    assert run.pr_number == 5
    assert run.head_sha == "h5"
    assert run.coverage_result_json == {}
    assert run.security_result_json == {}
    assert run.changed_files_snapshot_json[0]["filename"] == "a.py"
    assert run.diff_snapshot == "diff --git a/a.py b/a.py"


def test_build_pending_run_supports_webhook_trigger():
    run = _build_pending_run(
        uuid4(), _context(), AnalysisTriggerSource.GITHUB_WEBHOOK
    )

    assert run.trigger_source == AnalysisTriggerSource.GITHUB_WEBHOOK
    assert run.pull_request_snapshot_json["number"] == 5
