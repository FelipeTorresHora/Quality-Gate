import io
from datetime import UTC, datetime
import tarfile
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.models.enums import AnalysisRunStatus, GateDecision
from app.models.github_app_installation import GitHubAppInstallation
from app.models.installation_repository import InstallationRepository
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.schemas.repository import RepositoryCreate
from app.services import (
    analysis_evidence_workspace,
    github_oauth_service,
    repository_service,
    runtime_cache_service,
    token_crypto_service,
)
from app.services.agent.tools import collect_tool_results
from app.services.coverage_parsers.cobertura import parse_cobertura_xml
from app.services.coverage_parsers.types import CoverageFile
from app.services.dashboard_service import (
    _action_for_open_pull_request,
    _snapshot_html_url,
)
from app.services.gates import coverage_gate, security_gate, technical_debt_gate
from app.services.github_service import GitHubClient
from app.services.runner_service import (
    CommandResult,
    IsolatedRunnerWorkspace,
    RunnerWorkspace,
    _make_workspace_writable,
    _remove_container,
    download_repository_archive,
    RepositoryRef,
)
from app import worker


def test_runtime_cache_disabled_returns_none(monkeypatch):
    runtime_cache_service._get_cache.cache_clear()
    monkeypatch.setattr(
        runtime_cache_service,
        "get_settings",
        lambda: Settings(runtime_cache_enabled=False),
    )
    assert runtime_cache_service._get_cache() is None
    runtime_cache_service._get_cache.cache_clear()


def test_token_crypto_requires_encryption_key(monkeypatch):
    monkeypatch.delenv("TOKEN_ENCRYPTION_KEY", raising=False)
    token_crypto_service.get_settings.cache_clear()
    with pytest.raises(AppError) as exc:
        token_crypto_service.encrypt_token("x")
    assert exc.value.code == "token_encryption_key_missing"
    token_crypto_service.get_settings.cache_clear()


def test_security_normalize_scanner_branches():
    blocking = {"high"}
    assert security_gate._normalize_scanner(
        "detect-secrets", {"results": {}}, blocking
    ) == []
    assert security_gate._normalize_scanner("bandit", {"results": []}, blocking) == []
    assert security_gate._normalize_scanner("pip-audit", {"dependencies": []}, blocking) == []


def test_coverage_gate_is_source_file_variants():
    assert coverage_gate.is_source_file("docs/readme.md", "python") is False
    assert coverage_gate.is_source_file("src/.hidden.py", "python") is False
    assert coverage_gate.is_source_file("src/app.ts", "typescript") is True
    assert coverage_gate.is_source_file("src/app.test.ts", "typescript") is False
    assert coverage_gate.is_source_file("src/app.js", "javascript") is True
    assert coverage_gate.is_source_file("pkg/main.go", "go") is True
    assert coverage_gate.is_source_file("pkg/main_test.go", "go") is False
    assert coverage_gate.is_source_file("README", "ruby") is False


def test_coverage_gate_parse_report_and_unmatched_warning(tmp_path):
    report = tmp_path / "cov.xml"
    report.write_text(
        """<?xml version="1.0"?>
<coverage line-rate="0.5"><packages><package><classes>
<class filename="a.py" line-rate="0.5"><lines>
<line number="1" hits="1"/><line number="2" hits="0"/>
</lines></class></classes></package></packages></coverage>"""
    )
    parsed = coverage_gate._parse_report(report, "cobertura_xml")
    assert parsed.total_coverage == 50

    with pytest.raises(ValueError):
        coverage_gate._parse_report(report, "unknown")

    snapshot, findings = coverage_gate.apply_coverage_policy(
        language="python",
        report_format="cobertura_xml",
        base_sha="b",
        head_sha="h",
        base_coverage=90,
        pr_coverage=80,
        changed_files_coverage=70,
        changed_source_files=["missing.py"],
        unmatched=["missing.py"],
        quality_config={
            "min_total_coverage": 0,
            "max_coverage_drop": 100,
            "min_changed_files_coverage": 0,
        },
        command_metadata=[],
    )
    assert snapshot["warnings"]


def test_cobertura_parser_skips_missing_filename_and_merges_classes(tmp_path):
    report = tmp_path / "bad.xml"
    report.write_text(
        """<?xml version="1.0"?>
<coverage>
<packages><package><classes>
<class line-rate="0"><lines><line number="1" hits="0"/></lines></class>
<class filename="a.py"><lines><line number="1" hits="1"/></lines></class>
<class filename="a.py"><lines><line number="2" hits="0"/></lines></class>
</classes></package></packages></coverage>"""
    )
    result = parse_cobertura_xml(report)
    assert result.files["a.py"].total == 2


def test_coverage_file_percentage_when_total_zero():
    assert CoverageFile(covered=0, total=0).percentage == 0


def test_collect_tool_results_uses_first_changed_file_when_no_blocking():
    evidence = {
        "findings": [],
        "changed_files": [{"filename": "app/x.py", "patch": "+1"}],
        "gate_results": {},
    }
    results = collect_tool_results(evidence)
    assert results["get_changed_file_hunk"][0]["filename"] == "app/x.py"


def test_technical_debt_gate_python_and_brace_paths(monkeypatch, tmp_path):
    py_file = tmp_path / "app.py"
    py_file.write_text(
        "def tiny():\n"
        "    return 1\n"
    )
    js_file = tmp_path / "app.js"
    js_file.write_text("function big() {\n" + "  return 1;\n" * 50 + "}\n")

    class FakeHead:
        def __init__(self, root):
            self.root = root

        def path_in_repository(self, relative):
            return self.root / relative

    class FakeWorkspace:
        def prepare_head(self):
            return FakeHead(tmp_path)

    run = SimpleNamespace(
        changed_files_snapshot_json=[
            {"filename": "app.py", "patch": "@@ +1 @@\n+pass"},
            {"filename": "app.js", "patch": "@@ +1 @@\n+pass"},
        ],
        diff_snapshot="diff",
    )
    quality = SimpleNamespace(
        fail_on_new_todo=False,
        max_function_lines=1,
        max_complexity=1,
    )

    result_py = technical_debt_gate.run_technical_debt_gate(
        analysis_run=run,
        quality_config=quality,
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="python")),
        evidence_workspace=FakeWorkspace(),
    )
    assert result_py.findings

    result_js = technical_debt_gate.run_technical_debt_gate(
        analysis_run=run,
        quality_config=quality,
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="javascript")),
        evidence_workspace=FakeWorkspace(),
    )
    assert result_js.findings


def test_technical_debt_gate_diff_validation_and_runner_error():
    run = SimpleNamespace(changed_files_snapshot_json=[], diff_snapshot=None)
    result = technical_debt_gate.run_technical_debt_gate(
        analysis_run=run,
        quality_config=SimpleNamespace(fail_on_new_todo=False),
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="python")),
        evidence_workspace=SimpleNamespace(
            prepare_head=lambda: (_ for _ in ()).throw(
                __import__(
                    "app.services.runner_service", fromlist=["RunnerError"]
                ).RunnerError("fail")
            )
        ),
    )
    assert result.snapshot["status"] == "error"


def test_technical_debt_gate_syntax_error_returns_error(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("def oops(\n")

    class FakeHead:
        def path_in_repository(self, relative):
            return tmp_path / relative

    class FakeWorkspace:
        def prepare_head(self):
            return FakeHead()

    run = SimpleNamespace(
        changed_files_snapshot_json=[
            {"filename": "bad.py", "patch": "@@ +1 @@\n+bad"},
        ],
        diff_snapshot="diff",
    )
    result = technical_debt_gate.run_technical_debt_gate(
        analysis_run=run,
        quality_config=SimpleNamespace(
            fail_on_new_todo=False,
            max_function_lines=80,
            max_complexity=10,
        ),
        coverage_config=SimpleNamespace(language=SimpleNamespace(value="python")),
        evidence_workspace=FakeWorkspace(),
    )
    assert result.snapshot["status"] == "error"


def test_evidence_workspace_prepare_base_and_path_guard(monkeypatch, tmp_path):
    from app.models.analysis_run import AnalysisRun
    from app.models.enums import AnalysisTriggerSource
    from app.models.repository import Repository

    run = AnalysisRun(
        repository_id=uuid4(),
        pr_number=1,
        head_sha="head",
        status=AnalysisRunStatus.PENDING,
        trigger_source=AnalysisTriggerSource.MANUAL,
        pull_request_snapshot_json={"base_sha": "base"},
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
        head = ws.prepare_head()
        base = ws.prepare_base()
        assert head.repo_path.exists()
        assert base.repo_path.exists()
        with pytest.raises(Exception):
            head.path_in_working_directory("..", "escape")


def test_github_client_raise_for_response_variants():
    client = GitHubClient("token")

    rate = httpx.Response(
        403,
        headers={"x-ratelimit-remaining": "0"},
        request=httpx.Request("GET", "https://api.github.com"),
    )
    with pytest.raises(AppError) as exc:
        client._raise_for_response(rate, "o", "r")
    assert exc.value.code == "github_rate_limited"

    forbidden = httpx.Response(
        403,
        request=httpx.Request("GET", "https://api.github.com"),
    )
    with pytest.raises(AppError):
        client._raise_for_response(forbidden, "o", "r")

    not_found = httpx.Response(
        404,
        request=httpx.Request("GET", "https://api.github.com"),
    )
    with pytest.raises(AppError):
        client._raise_for_response(not_found, "o", "r")

    server_error = httpx.Response(
        500,
        request=httpx.Request("GET", "https://api.github.com"),
    )
    with pytest.raises(AppError):
        client._raise_for_response(server_error, "o", "r")


def test_list_pull_requests_without_github_repo_id(reset_database, db_session):
    from app.services import github_service

    repo = Repository(
        owner="local",
        name="only",
        full_name="local/only",
        default_branch="main",
        github_repo_id=None,
    )
    db_session.add(repo)
    db_session.commit()
    assert github_service.list_repository_pull_requests(db_session, repo.id) == []


def test_oauth_exchange_user_response_error(monkeypatch, reset_database, db_session):
    created = github_oauth_service.create_oauth_state(db_session)
    monkeypatch.setenv("GITHUB_APP_CLIENT_ID", "c")
    monkeypatch.setenv("GITHUB_APP_CLIENT_SECRET", "s")
    github_oauth_service.get_settings.cache_clear()

    class TokenResponse:
        is_error = False

        def json(self):
            return {"access_token": "tok"}

    class UserResponse:
        is_error = True

        def json(self):
            return {}

    monkeypatch.setattr(
        github_oauth_service.httpx, "post", lambda *a, **k: TokenResponse()
    )
    monkeypatch.setattr(
        github_oauth_service.httpx, "get", lambda *a, **k: UserResponse()
    )
    with pytest.raises(AppError):
        github_oauth_service.exchange_code_for_user(
            "code", created.state, db_session
        )
    github_oauth_service.get_settings.cache_clear()


def test_create_repository_integrity_error(reset_database, db_session):
    repository_service.create_repository(
        db_session,
        RepositoryCreate(
            owner="octo",
            name="first",
            full_name="octo/first",
            github_repo_id=1001,
        ),
    )
    with pytest.raises(AppError) as exc:
        repository_service.create_repository(
            db_session,
            RepositoryCreate(
                owner="octo",
                name="second",
                full_name="octo/second",
                github_repo_id=1001,
            ),
        )
    assert exc.value.code == "repository_already_exists"


def test_remove_installation_repositories_with_links(reset_database, db_session):
    from app.services import github_installation_service

    user = User(github_user_id=9, github_login="u")
    repo = Repository(
        github_repo_id=50,
        owner="o",
        name="r",
        full_name="o/r",
        default_branch="main",
    )
    installation = GitHubAppInstallation(
        installation_id=77,
        account_id=1,
        account_login="o",
        account_type="User",
        repository_selection="selected",
        permissions_json={},
        events_json=[],
        active=True,
    )
    db_session.add_all([user, repo, installation])
    db_session.flush()
    db_session.add(
        InstallationRepository(
            installation_id=installation.id,
            repository_id=repo.id,
            github_repo_id=50,
            full_name="o/r",
        )
    )
    db_session.add(
        UserRepositoryAccess(
            user_id=user.id,
            repository_id=repo.id,
            installation_id=installation.id,
            permission="admin",
            is_admin=True,
            synced_at=datetime.now(UTC),
        )
    )
    db_session.commit()
    github_installation_service.remove_installation_repositories(
        db_session, 77, {50}
    )
    assert db_session.query(InstallationRepository).count() == 0


def test_dashboard_action_helpers():
    run = SimpleNamespace(
        status=AnalysisRunStatus.COMPLETED,
        decision=GateDecision.FAIL,
        head_sha="abc",
    )
    assert (
        _action_for_open_pull_request(
            run, "outdated", comment_on_github=True, publish_github_status=True
        )
        == "outdated"
    )
    assert (
        _action_for_open_pull_request(
            run,
            "current",
            comment_on_github=False,
            publish_github_status=False,
        )
        == "publication_off"
    )
    assert _snapshot_html_url(None) is None
    assert _snapshot_html_url({"html_url": 1}) is None


def test_runner_workspace_removes_existing_root(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    existing = work / str(uuid4())
    existing.mkdir()
    run_id = uuid4()
    (work / str(run_id)).mkdir()

    monkeypatch.setattr(
        "app.services.runner_service.download_repository_archive",
        lambda *args, **kwargs: CommandResult(
            command="d",
            exit_code=0,
            stdout="",
            stderr="",
            duration_seconds=0.01,
        ),
    )

    with RunnerWorkspace(
        run_id,
        "https://github.com/o/r.git",
        settings=Settings(workdir=str(work), keep_workdir=True),
    ) as ws:
        ws.repo_path.mkdir(parents=True, exist_ok=True)
        ws.checkout("main")
        assert ws.root.exists()


def test_download_archive_bad_layout(monkeypatch, tmp_path):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        data = b"x"
        for name in ("a.txt", "b.txt"):
            info = tarfile.TarInfo(name=name)
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
    result = download_repository_archive(
        RepositoryRef("o", "r"),
        "sha",
        tmp_path / "repo",
        root,
    )
    assert result.exit_code == 1


def test_remove_container_swallows_errors(monkeypatch):
    monkeypatch.setattr(
        "app.services.runner_service.subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()),
    )
    _remove_container("missing")


def test_make_workspace_writable_skips_os_errors(tmp_path):
    path = tmp_path / "ro"
    path.mkdir()
    _make_workspace_writable(path)
