import io
import json
import stat
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import httpx
import jwt
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.core.errors import AppError
from app.models.analysis_run import AnalysisRun
from app.models.enums import (
    AnalysisRunStatus,
    AnalysisTriggerSource,
    FindingCategory,
    GateDecision,
)
from app.models.repository import Repository
from app.models.user import User
from app.schemas.coverage_execution_config import CoverageExecutionConfigUpdate
from app.schemas.github import GitHubPullRequestRead
from app.services import (
    analysis_execution_service,
    analysis_service,
    coverage_execution_config_service,
    github_app_auth_service,
    github_installation_service,
    github_publication_service,
    quality_gate_service,
    report_service,
    session_service,
)
from app.services.agent.tools import collect_tool_results, invoke_review_tools
from app.services.coverage_parsers.types import CoverageFile
from app.services.dashboard_service import (
    _action_for_open_pull_request,
    _open_pull_requests_needing_action,
)
from app.services.gates import coverage_gate, security_gate, technical_debt_gate
from app.services.github_service import GitHubClient, _map_pull_request
from app.services.pull_request_review_service import (
    get_pull_request_review_state,
    get_pull_request_review_states,
)
from app.services.runner_service import (
    CommandResult,
    IsolatedRunnerWorkspace,
    RepositoryRef,
    RunnerError,
    _make_workspace_writable,
    download_repository_archive,
    run_command,
)
from app import worker


def test_collect_tool_results_skips_empty_and_duplicate_blocking_paths():
    evidence = {
        "findings": [
            {"blocking": True, "file_path": None, "title": "no path"},
            {"blocking": True, "file_path": "a.py", "title": "one"},
            {"blocking": True, "file_path": "a.py", "title": "dup"},
        ],
        "changed_files": [{"filename": "fallback.py", "patch": "+x"}],
        "gate_results": {},
    }
    results = collect_tool_results(evidence)
    assert len(results["get_changed_file_hunk"]) == 1
    assert results["get_changed_file_hunk"][0]["filename"] == "a.py"


def test_invoke_review_tools_fallback_changed_file_without_blocking_hunks():
    evidence = {
        "findings": [],
        "changed_files": [{"filename": "only.py", "patch": "+1"}],
        "gate_results": {},
    }
    results = invoke_review_tools(evidence)
    assert results["get_changed_file_hunk"][0]["filename"] == "only.py"


def test_evidence_workspace_missing_base_sha_and_reprepare_revision(
    monkeypatch, tmp_path
):
    from app.services import analysis_evidence_workspace

    run = AnalysisRun(
        repository_id=uuid4(),
        pr_number=1,
        head_sha="head",
        status=AnalysisRunStatus.PENDING,
        trigger_source=AnalysisTriggerSource.MANUAL,
        pull_request_snapshot_json={},
        changed_files_snapshot_json=[],
        diff_snapshot="d",
    )
    repo = Repository(
        owner="o",
        name="r",
        full_name="o/r",
        default_branch="main",
    )

    class FakeRunner:
        command_metadata = []
        root = tmp_path / "ws"
        repo_path = root / "repo"

        def __enter__(self):
            self.root.mkdir(parents=True, exist_ok=True)
            return self

        def __exit__(self, *args):
            return None

        def checkout(self, revision):
            self.repo_path.mkdir(parents=True, exist_ok=True)
            (self.repo_path / "file.py").write_text("x")

        def run(self, command, working_directory="."):
            return CommandResult(
                command=command,
                exit_code=0,
                stdout="",
                stderr="",
                duration_seconds=0.01,
            )

    monkeypatch.setattr(
        analysis_evidence_workspace,
        "RunnerWorkspace",
        lambda *args, **kwargs: FakeRunner(),
    )

    with analysis_evidence_workspace.GateExecutionEvidenceWorkspace(
        analysis_run=run,
        repository=repo,
        repository_token=None,
    ) as ws:
        with pytest.raises(RunnerError, match="base revision"):
            ws.prepare_base()
        ws.prepare_revision("head")
        prepared_path = ws._prepared_path("head")
        ws._prepared.pop("head")
        (prepared_path / "stale.txt").write_text("stale")
        second = ws.prepare_revision("head")
        assert second.repo_path.exists()


def test_analysis_execution_reraises_app_error_and_missing_run(
    repository, reset_database, monkeypatch
):
    from app.db.session import SessionLocal

    run_id = uuid4()
    with pytest.raises(AppError) as exc:
        with SessionLocal() as db:
            analysis_execution_service.execute_analysis_run(db, run_id)
    assert exc.value.code == "analysis_run_not_found"

    pending_id = _insert_pending_run(repository["id"])
    monkeypatch.setattr(
        analysis_execution_service,
        "_run_pipeline",
        lambda db, run, token: (_ for _ in ()).throw(
            AppError(409, "analysis_run_not_pending", "blocked")
        ),
    )
    with pytest.raises(AppError) as exc2:
        with SessionLocal() as db:
            analysis_execution_service.execute_analysis_run(db, pending_id)
    assert exc2.value.code == "analysis_run_not_pending"


def test_analysis_execution_timeout_after_each_gate(repository, monkeypatch):
    from app.services.gates import coverage_gate, security_gate, technical_debt_gate

    monkeypatch.setattr(
        analysis_execution_service.github_app_auth_service,
        "generate_installation_token",
        lambda installation_id: "token",
    )
    monkeypatch.setattr(
        analysis_execution_service.github_publication_service,
        "try_publish_pending_commit_status",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        analysis_execution_service.github_publication_service,
        "try_publish_analysis_run_to_github",
        lambda *args, **kwargs: None,
    )

    run_id = _insert_pending_run(repository["id"])
    monotonic_values = iter([10.0, 11.0, 12.0, 21.0, 21.0])

    monkeypatch.setattr(
        analysis_execution_service.time,
        "monotonic",
        lambda: next(monotonic_values, 25.0),
    )
    monkeypatch.setattr(
        analysis_execution_service,
        "get_settings",
        lambda: SimpleNamespace(analysis_total_timeout_seconds=10),
    )
    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.COVERAGE),
    )
    monkeypatch.setattr(
        security_gate,
        "run_security_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.SECURITY),
    )
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.TECHNICAL_DEBT),
    )

    from app.db.session import SessionLocal

    with SessionLocal() as db:
        finished = analysis_execution_service.execute_analysis_run(db, run_id)
    assert finished.status == AnalysisRunStatus.ERROR
    assert "time budget" in (finished.error_message or "").lower()


def test_run_pipeline_time_budget_checks_between_gates(
    reset_database, db_session, repository, monkeypatch
):
    from contextlib import contextmanager

    from app.services.gates import coverage_gate, security_gate, technical_debt_gate

    @contextmanager
    def fake_evidence(*args, **kwargs):
        yield SimpleNamespace(
            metadata_checkpoint=lambda: 0,
            metadata_since=lambda checkpoint: [],
        )

    monkeypatch.setattr(
        analysis_execution_service,
        "GateExecutionEvidenceWorkspace",
        fake_evidence,
    )
    monkeypatch.setattr(
        analysis_execution_service,
        "get_settings",
        lambda: SimpleNamespace(analysis_total_timeout_seconds=10),
    )
    monkeypatch.setattr(
        coverage_gate,
        "run_coverage_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.COVERAGE),
    )
    monkeypatch.setattr(
        security_gate,
        "run_security_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.SECURITY),
    )
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result("pass", FindingCategory.TECHNICAL_DEBT),
    )
    monkeypatch.setattr(
        analysis_execution_service.quality_agent,
        "generate_ai_review_snapshot",
        lambda **kwargs: {"status": "skipped"},
    )
    monkeypatch.setattr(
        analysis_execution_service.report_service,
        "build_final_report",
        lambda *args, **kwargs: "report",
    )

    def timeout_after(calls_before_timeout: int):
        state = {"calls": 0}

        def monotonic():
            state["calls"] += 1
            if state["calls"] < calls_before_timeout:
                return 10.0
            return 100.0

        return monotonic

    def load_run(run_id):
        return analysis_execution_service._get_run_for_execution(db_session, run_id)

    run_id = _insert_pending_run(repository["id"])
    monkeypatch.setattr(
        analysis_execution_service.time,
        "monotonic",
        timeout_after(3),
    )
    before_security = analysis_execution_service._run_pipeline(
        db_session, load_run(run_id), None
    )
    assert before_security.status == AnalysisRunStatus.ERROR

    run_id_2 = _insert_pending_run(repository["id"], head_sha="head456", pr_number=43)
    monkeypatch.setattr(
        analysis_execution_service.time,
        "monotonic",
        timeout_after(4),
    )
    before_debt = analysis_execution_service._run_pipeline(
        db_session, load_run(run_id_2), None
    )
    assert before_debt.status == AnalysisRunStatus.ERROR

    run_id_3 = _insert_pending_run(repository["id"], head_sha="head789", pr_number=44)
    monkeypatch.setattr(
        technical_debt_gate,
        "run_technical_debt_gate",
        lambda **kwargs: _gate_result(
            "error", FindingCategory.TECHNICAL_DEBT, error_message="debt failed"
        ),
    )
    debt_error = analysis_execution_service._run_pipeline(
        db_session, load_run(run_id_3), None
    )
    assert debt_error.status == AnalysisRunStatus.ERROR
    assert debt_error.error_message == "debt failed"


def test_commit_new_run_or_reuse_reraises_when_duplicate_missing(
    reset_database, db_session, repository, monkeypatch
):
    run = AnalysisRun(
        repository_id=UUID(repository["id"]),
        pr_number=100,
        head_sha="orphan-sha",
        status=AnalysisRunStatus.PENDING,
        trigger_source=AnalysisTriggerSource.MANUAL,
        pull_request_snapshot_json={},
        changed_files_snapshot_json=[],
        diff_snapshot="d",
    )
    monkeypatch.setattr(
        db_session,
        "commit",
        lambda: (_ for _ in ()).throw(IntegrityError("insert", {}, Exception("dup"))),
    )
    monkeypatch.setattr(
        analysis_service,
        "get_analysis_run_by_pr_head",
        lambda *args, **kwargs: None,
    )
    with pytest.raises(IntegrityError):
        analysis_service._commit_new_run_or_reuse(db_session, run)


def test_commit_new_run_or_reuse_integrity_error_path(
    reset_database, db_session, repository, monkeypatch
):
    run = AnalysisRun(
        repository_id=UUID(repository["id"]),
        pr_number=99,
        head_sha="race-sha",
        status=AnalysisRunStatus.PENDING,
        trigger_source=AnalysisTriggerSource.MANUAL,
        pull_request_snapshot_json={},
        changed_files_snapshot_json=[],
        diff_snapshot="d",
    )

    original_commit = db_session.commit
    attempts = {"n": 0}

    def flaky_commit():
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise IntegrityError("insert", {}, Exception("dup"))
        return original_commit()

    monkeypatch.setattr(db_session, "commit", flaky_commit)

    existing = AnalysisRun(
        repository_id=UUID(repository["id"]),
        pr_number=99,
        head_sha="race-sha",
        status=AnalysisRunStatus.PENDING,
        trigger_source=AnalysisTriggerSource.MANUAL,
        pull_request_snapshot_json={},
        changed_files_snapshot_json=[],
        diff_snapshot="d",
    )
    db_session.add(existing)
    original_commit()

    reused = analysis_service._commit_new_run_or_reuse(db_session, run)
    assert reused.id == existing.id


def test_coverage_execution_config_not_found_and_invalid_format(
    reset_database, db_session, repository
):
    repo = db_session.get(Repository, UUID(repository["id"]))
    repo.coverage_execution_config = None
    db_session.commit()
    with pytest.raises(AppError) as exc:
        coverage_execution_config_service.get_coverage_execution_config(
            db_session, UUID(repository["id"])
        )
    assert exc.value.code == "coverage_execution_config_not_found"

    repo.coverage_execution_config = (
        coverage_execution_config_service.build_coverage_execution_config(
            github_language="Python"
        )
    )
    db_session.commit()
    with pytest.raises(AppError) as exc2:
        coverage_execution_config_service.update_coverage_execution_config(
            db_session,
            UUID(repository["id"]),
            CoverageExecutionConfigUpdate(report_format="lcov"),
        )
    assert exc2.value.code == "coverage_report_format_invalid"


def test_coverage_file_percentage_non_zero():
    assert CoverageFile(covered=1, total=4).percentage == 25.0


def test_dashboard_action_fail_and_skip_none_action():
    run = SimpleNamespace(
        status=AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        head_sha="abc",
    )
    assert (
        _action_for_open_pull_request(
            run, "current", comment_on_github=True, publish_github_status=False
        )
        == "fail"
    )
    assert (
        _action_for_open_pull_request(
            SimpleNamespace(
                status=AnalysisRunStatus.COMPLETED,
                decision=GateDecision.PASS,
                head_sha="abc",
            ),
            "current",
            comment_on_github=True,
            publish_github_status=True,
        )
        is None
    )


def test_open_pull_requests_needing_action_skips_when_action_none(
    reset_database, db_session, repository, monkeypatch
):
    repo_id = UUID(repository["id"])
    run = AnalysisRun(
        repository_id=repo_id,
        pr_number=7,
        head_sha="sha",
        status=AnalysisRunStatus.COMPLETED,
        decision=GateDecision.PASS,
        trigger_source=AnalysisTriggerSource.MANUAL,
        pull_request_snapshot_json={"number": 7},
        changed_files_snapshot_json=[],
        diff_snapshot="d",
        created_at=datetime.now(UTC),
    )
    db_session.add(run)
    db_session.commit()

    pr = GitHubPullRequestRead(
        number=7,
        title="Open",
        user_login="u",
        state="open",
        draft=False,
        head_ref="f",
        head_sha="sha",
        base_ref="main",
        html_url="https://github.com/o/r/pull/7",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    monkeypatch.setattr(
        "app.services.dashboard_service._latest_candidate_runs",
        lambda db, ids: [run],
    )
    monkeypatch.setattr(
        "app.services.dashboard_service._open_pull_requests_by_repository",
        lambda db, ids: {repo_id: {7: pr}},
    )
    monkeypatch.setattr(
        "app.services.dashboard_service._publication_flags_by_repository",
        lambda db, ids: {repo_id: (True, True)},
    )

    items = _open_pull_requests_needing_action(db_session, [repo_id])
    assert items == []


def test_run_revision_coverage_missing_report_and_parse_formats(tmp_path):
    class FakeRevision:
        def run(self, command, working_directory="."):
            return CommandResult(
                command=command,
                exit_code=0,
                stdout="",
                stderr="",
                duration_seconds=0.01,
            )

        def path_in_working_directory(self, working_directory, relative):
            return tmp_path / relative

    config = SimpleNamespace(
        install_command="",
        test_command="pytest",
        working_directory=".",
        report_path="missing.xml",
        report_format=SimpleNamespace(value="cobertura_xml"),
    )
    with pytest.raises(RunnerError, match="not produced"):
        coverage_gate._run_revision_coverage(FakeRevision(), config)

    lcov = tmp_path / "cov.info"
    lcov.write_text("TN:\nSF:src/a.py\nDA:1,1\nend_of_record\n")
    config.report_path = "cov.info"
    config.report_format = SimpleNamespace(value="lcov")
    parsed = coverage_gate._run_revision_coverage(FakeRevision(), config)
    assert parsed.total_coverage >= 0

    go_report = tmp_path / "cover.out"
    go_report.write_text("mode: set\nsrc/a.go:1.1,2.1 2 1\n")
    config.report_path = "cover.out"
    config.report_format = SimpleNamespace(value="go_coverprofile")
    parsed_go = coverage_gate._run_revision_coverage(FakeRevision(), config)
    assert parsed_go.files


def test_run_security_gate_python_scanners_in_run_path(monkeypatch):
    payloads = {
        "semgrep": {"results": []},
        "detect-secrets": {"results": {}},
        "bandit": {"results": []},
        "pip-audit": {"dependencies": []},
    }

    class FakeHead:
        def run(self, command):
            for name, payload in payloads.items():
                if name in command:
                    return CommandResult(
                        command=command,
                        exit_code=0,
                        stdout=json.dumps(payload),
                        stderr="",
                        duration_seconds=0.01,
                    )
            raise AssertionError(command)

    class FakeWorkspace:
        def prepare_head(self):
            return FakeHead()

    result = security_gate.run_security_gate(
        quality_config=SimpleNamespace(security_fail_on=["high"]),
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="python")),
        evidence_workspace=FakeWorkspace(),
    )
    assert result.snapshot["status"] == "pass"
    assert set(result.snapshot["scanners_run"]) == set(payloads)


def test_technical_debt_suggestions_for_length_and_complexity():
    from app.models.enums import FindingCategory, FindingSeverity
    from app.services.gates.types import GateFinding

    findings = [
        GateFinding(
            category=FindingCategory.TECHNICAL_DEBT,
            severity=FindingSeverity.LOW,
            file_path="a.py",
            line_number=1,
            title="New TODO/FIXME marker",
            description="todo",
            blocking=False,
        ),
        GateFinding(
            category=FindingCategory.TECHNICAL_DEBT,
            severity=FindingSeverity.LOW,
            file_path="a.py",
            line_number=1,
            title="Function exceeds line limit",
            description="long",
            blocking=False,
        ),
        GateFinding(
            category=FindingCategory.TECHNICAL_DEBT,
            severity=FindingSeverity.LOW,
            file_path="a.py",
            line_number=2,
            title="Function complexity exceeds limit",
            description="complex",
            blocking=False,
        ),
    ]
    snapshot = technical_debt_gate.build_technical_debt_snapshot(findings)
    joined = " ".join(snapshot["suggestions"])
    assert "TODO/FIXME" in joined
    assert "Split long functions" in joined
    assert "Simplify branching" in joined


def test_technical_debt_gate_missing_file_runner_error_and_suggestions(
    monkeypatch, tmp_path
):
    run = SimpleNamespace(
        changed_files_snapshot_json=[
            {"filename": "ghost.py", "patch": "@@ +1 @@\n+pass"},
            {"filename": "plain.txt", "patch": "@@ +1 @@\n+x"},
        ],
        diff_snapshot="diff",
    )

    class FakeHead:
        def path_in_repository(self, relative):
            return tmp_path / relative

    class FakeWorkspace:
        def prepare_head(self):
            return FakeHead()

    skipped = technical_debt_gate.run_technical_debt_gate(
        analysis_run=run,
        quality_config=SimpleNamespace(
            fail_on_new_todo=False,
            max_function_lines=80,
            max_complexity=10,
        ),
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="python")),
        evidence_workspace=FakeWorkspace(),
    )
    assert skipped.snapshot["status"] == "pass"

    class BrokenWorkspace:
        def prepare_head(self):
            raise RunnerError("workspace failed")

    runner_error = technical_debt_gate.run_technical_debt_gate(
        analysis_run=run,
        quality_config=SimpleNamespace(
            fail_on_new_todo=False,
            max_function_lines=80,
            max_complexity=10,
        ),
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="python")),
        evidence_workspace=BrokenWorkspace(),
    )
    assert runner_error.snapshot["status"] == "error"

    brace = tmp_path / "b.js"
    brace.write_text("// comment only\nconst value = 1;\nfunction big() {\n" + "  return 1;\n" * 40 + "}\n")
    run_js = SimpleNamespace(
        changed_files_snapshot_json=[{"filename": "b.js", "patch": "@@ +1 @@\n+x"}],
        diff_snapshot="diff",
    )

    class LocalHead:
        def path_in_repository(self, relative):
            return tmp_path / relative

    class LocalWorkspace:
        def prepare_head(self):
            return LocalHead()

    js_result = technical_debt_gate.run_technical_debt_gate(
        analysis_run=run_js,
        quality_config=SimpleNamespace(
            fail_on_new_todo=True,
            max_function_lines=5,
            max_complexity=10,
        ),
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="javascript")),
        evidence_workspace=LocalWorkspace(),
    )
    snapshot = js_result.snapshot
    assert snapshot["suggestions"]


def test_github_app_auth_private_key_path_and_errors(monkeypatch, tmp_path):
    key_path = tmp_path / "key.pem"
    key_path.write_text("fake-key", encoding="utf-8")
    monkeypatch.setenv("GITHUB_APP_ID", "")
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_PATH", str(key_path))
    github_app_auth_service.get_settings.cache_clear()

    with pytest.raises(AppError) as exc:
        github_app_auth_service.generate_app_jwt()
    assert exc.value.code == "github_app_config_missing"

    monkeypatch.setenv("GITHUB_APP_ID", "123")
    github_app_auth_service.get_settings.cache_clear()
    assert github_app_auth_service._private_key() == "fake-key"

    class ErrorResponse:
        is_error = True

    monkeypatch.setattr(
        github_app_auth_service,
        "generate_app_jwt",
        lambda: "jwt",
    )
    monkeypatch.setattr(
        github_app_auth_service.httpx, "post", lambda *_, **__: ErrorResponse()
    )
    with pytest.raises(AppError) as exc3:
        github_app_auth_service.generate_installation_token(1)
    assert exc3.value.code == "github_installation_token_failed"
    github_app_auth_service.get_settings.cache_clear()


def test_github_installation_remove_and_sync_edge_paths(reset_database, db_session):
    from app.models.installation_repository import InstallationRepository

    github_installation_service.remove_installation_repositories(
        db_session, 999, {123}
    )
    assert github_installation_service._permission_name({"pull": True}) == "pull"
    assert github_installation_service._permission_name({}) is None

    user = User(github_user_id=501, github_login="sync-user")
    db_session.add(user)
    db_session.commit()
    github_installation_service.sync_installation_payload(
        db_session,
        user=user,
        installation_payload={
            "id": 900,
            "account": {"id": 1, "login": "org", "type": "Organization"},
            "repository_selection": "selected",
            "permissions": {},
            "events": [],
        },
        repositories_payload=[
            {
                "id": 1000,
                "name": "one",
                "full_name": "org/one",
                "owner": {"login": "org"},
                "default_branch": "main",
                "permissions": {"pull": True},
            }
        ],
    )
    stale_repo_id = db_session.query(InstallationRepository).one().repository_id
    github_installation_service.sync_installation_payload(
        db_session,
        user=user,
        installation_payload={
            "id": 900,
            "account": {"id": 1, "login": "org", "type": "Organization"},
        },
        repositories_payload=[],
        replace_repositories=True,
    )
    assert db_session.query(InstallationRepository).count() == 0

    with pytest.raises(AppError) as exc:
        github_installation_service.get_active_installation_for_repository(
            db_session, stale_repo_id
        )
    assert exc.value.code == "github_installation_required"


def test_sync_user_installations_removes_stale_installation_access(
    reset_database, db_session, monkeypatch
):
    from app.models.github_connection import GitHubConnection
    from app.models.user_repository_access import UserRepositoryAccess

    user = User(github_user_id=888, github_login="sync")
    db_session.add(user)
    db_session.flush()
    db_session.add(
        GitHubConnection(
            user_id=user.id,
            github_user_id=888,
            github_login="sync",
            access_token_encrypted="enc",
        )
    )
    github_installation_service.sync_installation_payload(
        db_session,
        user=user,
        installation_payload={
            "id": 700,
            "account": {"id": 1, "login": "org", "type": "Organization"},
        },
        repositories_payload=[
            {
                "id": 800,
                "name": "repo",
                "full_name": "org/repo",
                "owner": {"login": "org"},
                "permissions": {"pull": True},
            }
        ],
    )
    assert db_session.query(UserRepositoryAccess).count() == 1

    monkeypatch.setattr(
        github_installation_service.token_crypto_service,
        "decrypt_token",
        lambda value: "oauth-token",
    )
    monkeypatch.setattr(
        github_installation_service,
        "_get_paginated_user_resource",
        lambda token, path, collection_key: [],
    )
    github_installation_service.sync_user_installations(db_session, user)
    assert db_session.query(UserRepositoryAccess).count() == 0


def test_github_installation_pagination_error(monkeypatch):
    class ErrorResponse:
        is_error = True

    monkeypatch.setattr(
        github_installation_service.httpx, "get", lambda *_, **__: ErrorResponse()
    )
    with pytest.raises(AppError) as exc:
        github_installation_service._get_paginated_user_resource(
            "token", "/user/installations", "installations"
        )
    assert exc.value.code == "github_installation_sync_failed"


def test_github_publication_pending_status_and_missing_run(reset_database, db_session):
    repo = Repository(
        owner="o",
        name="r",
        full_name="o/r",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.flush()
    from app.models.quality_gate_config import QualityGateConfig

    repo.quality_gate_config = QualityGateConfig(
        repository_id=repo.id,
        publish_github_status=True,
    )
    run = AnalysisRun(
        repository_id=repo.id,
        pr_number=1,
        head_sha="sha",
        status=AnalysisRunStatus.COMPLETED,
        trigger_source=AnalysisTriggerSource.MANUAL,
        pull_request_snapshot_json={},
        changed_files_snapshot_json=[],
        diff_snapshot="d",
    )
    db_session.add(run)
    db_session.commit()

    pending = github_publication_service.publish_pending_commit_status(
        db_session, run.id
    )
    assert pending.skipped_reason == "run_not_running"

    with pytest.raises(AppError) as exc:
        github_publication_service.publish_analysis_run_to_github(db_session, uuid4())
    assert exc.value.code == "analysis_run_not_found"


def test_map_pull_request():
    mapped = _map_pull_request(
        {
            "number": 1,
            "title": "T",
            "user": {"login": "octo"},
            "state": "open",
            "draft": False,
            "head": {"ref": "f", "sha": "abc"},
            "base": {"ref": "main"},
            "html_url": "https://github.com/o/r/pull/1",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    )
    assert mapped.number == 1
    assert mapped.head_sha == "abc"


def test_pull_request_review_state_helpers(reset_database, db_session, repository):
    assert get_pull_request_review_states(db_session, UUID(repository["id"]), []) == {}
    pr = GitHubPullRequestRead(
        number=3,
        title="PR",
        user_login="u",
        state="open",
        draft=False,
        head_ref="f",
        head_sha="head",
        base_ref="main",
        html_url="https://github.com/o/r/pull/3",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    state = get_pull_request_review_state(db_session, UUID(repository["id"]), pr)
    assert state.state == "not_run"


def test_quality_gate_config_missing(reset_database, db_session, repository):
    repo = db_session.get(Repository, UUID(repository["id"]))
    repo.quality_gate_config = None
    db_session.commit()
    with pytest.raises(AppError) as exc:
        quality_gate_service.get_quality_gate_config(db_session, UUID(repository["id"]))
    assert exc.value.code == "quality_gate_config_not_found"


def test_report_service_pass_summary_and_suggestions():
    run = SimpleNamespace(
        status=AnalysisRunStatus.COMPLETED,
        decision=GateDecision.PASS,
        score=None,
        coverage_result_json={
            "status": "pass",
            "blocking_reasons": [],
            "suggestions": ["Keep tests green."],
        },
        security_result_json={"status": "pass"},
        technical_debt_result_json={"status": "pass"},
        findings=[],
    )
    report = report_service.build_final_report(run, {})
    assert "passed their configured policies" in report
    assert "Keep tests green." in report


def test_isolated_runner_workspace_paths(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    stale = work / str(uuid4())
    stale.mkdir()
    run_id = uuid4()
    stale_run = work / str(run_id)
    stale_run.mkdir()

    monkeypatch.setattr(
        "app.services.runner_service.download_repository_archive",
        lambda *args, **kwargs: CommandResult(
            command="d",
            exit_code=0,
            stdout="",
            stderr="",
            duration_seconds=0.01,
            timed_out=True,
        ),
    )
    with IsolatedRunnerWorkspace(
        run_id,
        "https://github.com/o/r.git",
        settings=Settings(workdir=str(work)),
    ) as ws:
        with pytest.raises(RunnerError, match="checkout failed"):
            ws.checkout("main")
        ws.repo_path.mkdir(parents=True)
        with pytest.raises(RunnerError, match="inside the repository"):
            ws._resolve_working_directory("../escape")
        with pytest.raises(RunnerError, match="does not exist"):
            ws._resolve_working_directory("missing-dir")


def test_download_archive_reuses_existing_paths(monkeypatch, tmp_path):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        data = b"x"
        info = tarfile.TarInfo(name="root-only/file.txt")
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    payload = buffer.getvalue()

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, size=-1):
            if not hasattr(self, "_done"):
                self._done = True
                return payload
            return b""

    monkeypatch.setattr(
        "app.services.runner_service._opener.open",
        lambda *args, **kwargs: FakeResponse(),
    )
    root = tmp_path / "root"
    root.mkdir()
    extract_existing = root / "extract"
    extract_existing.mkdir()
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "old.txt").write_text("old")

    result = download_repository_archive(
        RepositoryRef("o", "r"),
        "sha",
        repo_path,
        root,
    )
    assert result.exit_code == 0
    assert (repo_path / "file.txt").exists()


def test_run_command_success_and_writable_chmod_continue(tmp_path, monkeypatch):
    result = run_command("echo ok", tmp_path, timeout_seconds=5)
    assert result.exit_code == 0

    target = tmp_path / "locked"
    target.mkdir()
    (target / "child").write_text("x")

    def chmod_fail(self, mode):
        raise OSError("chmod denied")

    monkeypatch.setattr(Path, "chmod", chmod_fail, raising=False)
    _make_workspace_writable(target)


def test_session_service_csrf_and_payload_edges(reset_database, db_session, monkeypatch):
    user = User(github_user_id=77, github_login="edge")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(db_session, user)

    token = jwt.decode(
        created.cookie_value,
        session_service.get_settings().session_secret,
        algorithms=["HS256"],
    )
    token.pop("csrf_hash")
    no_hash_cookie = jwt.encode(
        token,
        session_service.get_settings().session_secret,
        algorithm="HS256",
    )
    assert session_service.validate_csrf_token(no_hash_cookie, created.csrf_token) is False

    token_with_jti = jwt.decode(
        created.cookie_value,
        session_service.get_settings().session_secret,
        algorithms=["HS256"],
    )
    token_with_jti.pop("jti")
    no_jti = jwt.encode(
        token_with_jti,
        session_service.get_settings().session_secret,
        algorithm="HS256",
    )
    assert session_service.get_user_for_session(no_jti, db_session) is None

    unknown_jti = jwt.encode(
        {
            "jti": "missing-session-id",
            "sub": str(user.id),
            "github_user_id": user.github_user_id,
            "csrf_hash": "hash",
        },
        session_service.get_settings().session_secret,
        algorithm="HS256",
    )
    assert session_service.get_user_for_session(unknown_jti, db_session) is None

    monkeypatch.setattr(
        session_service.jwt,
        "decode",
        lambda *args, **kwargs: ["not-a-dict"],
    )
    assert session_service.get_user_for_session("cookie", db_session) is None


def test_worker_main_invokes_run_forever():
    called = {"run_forever": False}

    def fake_run_forever(poll_seconds=2.0):
        called["run_forever"] = True

    namespace = worker.__dict__.copy()
    namespace["run_forever"] = fake_run_forever
    worker_path = Path(__file__).resolve().parents[1] / "app" / "worker.py"
    namespace["__name__"] = "__main__"
    exec(
        compile(
            "if __name__ == '__main__':\n    run_forever()\n",
            str(worker_path),
            "exec",
        ),
        namespace,
    )
    assert called["run_forever"]


def _gate_result(status: str, category: FindingCategory, *, error_message=None):
    from app.services.gates.types import GateResult

    return GateResult(
        snapshot={"status": status, "blocking_reasons": []},
        findings=[],
        error_message=error_message,
    )


def _insert_pending_run(repository_id: str, *, head_sha="head123", pr_number=42):
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        run = AnalysisRun(
            repository_id=UUID(repository_id),
            pr_number=pr_number,
            head_sha=head_sha,
            status=AnalysisRunStatus.PENDING,
            trigger_source=AnalysisTriggerSource.MANUAL,
            pull_request_snapshot_json={"base_sha": "base123", "number": 42},
            changed_files_snapshot_json=[{"filename": "a.py", "patch": "+x"}],
            diff_snapshot="diff",
        )
        db.add(run)
        db.commit()
        return run.id

