import io
import tarfile
import urllib.error
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.runner_service import (
    CommandResult,
    IsolatedRunnerWorkspace,
    RepositoryRef,
    RunnerError,
    RunnerWorkspace,
    create_runner_workspace,
    download_repository_archive,
    parse_repository_url,
    redacted_command,
    repository_clone_url,
    run_command,
    run_isolated_command,
    _validate_archive_members,
)


def test_repository_clone_url_with_and_without_token():
    assert repository_clone_url("octo", "repo") == "https://github.com/octo/repo.git"
    assert (
        repository_clone_url("octo", "repo", token="tok")
        == "https://x-access-token:tok@github.com/octo/repo.git"
    )


def test_parse_repository_url_extracts_token():
    ref = parse_repository_url(
        "https://x-access-token:ghs_secret@github.com/octo-org/quality-api.git"
    )
    assert ref.owner == "octo-org"
    assert ref.name == "quality-api"
    assert ref.token == "ghs_secret"


def test_parse_repository_url_rejects_non_github():
    with pytest.raises(RunnerError, match="Only GitHub"):
        parse_repository_url("https://gitlab.com/octo/repo.git")


def test_parse_repository_url_rejects_invalid_path():
    with pytest.raises(RunnerError, match="invalid"):
        parse_repository_url("https://github.com/only-owner")


def test_create_runner_workspace_local_in_development():
    workspace = create_runner_workspace(
        uuid4(),
        "https://github.com/octo/repo.git",
        settings=Settings(app_env="development", runner_adapter="local"),
    )
    assert isinstance(workspace, RunnerWorkspace)


def test_create_runner_workspace_unsupported_adapter():
    with pytest.raises(RunnerError, match="Unsupported"):
        create_runner_workspace(
            uuid4(),
            "https://github.com/octo/repo.git",
            settings=Settings(runner_adapter="kubernetes"),
        )


def test_redacted_command_masks_token():
    command = "git clone https://x-access-token:secret@github.com/o/r.git"
    assert "secret" not in redacted_command(command)
    assert "x-access-token:***@" in redacted_command(command)


def test_runner_workspace_checkout_and_run(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKDIR", str(tmp_path / "work"))
    run_id = uuid4()
    repo_url = "https://github.com/octo/repo.git"

    def fake_download(repository, revision, repo_path, root, timeout_seconds=None):
        repo_path.mkdir(parents=True, exist_ok=True)
        (repo_path / "nested").mkdir()
        (repo_path / "nested" / "file.txt").write_text("ok")
        return CommandResult(
            command="download",
            exit_code=0,
            stdout="ok",
            stderr="",
            duration_seconds=0.01,
        )

    monkeypatch.setattr(
        "app.services.runner_service.download_repository_archive", fake_download
    )

    def fake_run(command, cwd, timeout_seconds=None):
        return CommandResult(
            command=command,
            exit_code=0,
            stdout="hello",
            stderr="",
            duration_seconds=0.01,
            adapter="local",
        )

    monkeypatch.setattr("app.services.runner_service.run_command", fake_run)

    with RunnerWorkspace(
        run_id, repo_url, settings=Settings(workdir=str(tmp_path / "work"))
    ) as workspace:
        workspace.checkout("main")
        result = workspace.run("echo hello", working_directory="nested")
        assert result.exit_code == 0
        assert "hello" in result.stdout


def test_runner_workspace_checkout_failure_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.services.runner_service.download_repository_archive",
        lambda *args, **kwargs: CommandResult(
            command="download",
            exit_code=1,
            stdout="",
            stderr="fail",
            duration_seconds=0.01,
        ),
    )
    with RunnerWorkspace(
        uuid4(),
        "https://github.com/octo/repo.git",
        settings=Settings(workdir=str(tmp_path)),
    ) as workspace:
        with pytest.raises(RunnerError, match="checkout failed"):
            workspace.checkout("main")


def test_runner_workspace_rejects_escape_from_repo(tmp_path):
    with RunnerWorkspace(
        uuid4(),
        "https://github.com/octo/repo.git",
        settings=Settings(workdir=str(tmp_path)),
    ) as workspace:
        workspace.repo_path.mkdir(parents=True)
        with pytest.raises(RunnerError, match="inside the repository"):
            workspace._resolve_working_directory("../outside")


def test_runner_workspace_rejects_missing_working_directory(tmp_path):
    with RunnerWorkspace(
        uuid4(),
        "https://github.com/octo/repo.git",
        settings=Settings(workdir=str(tmp_path)),
    ) as workspace:
        workspace.repo_path.mkdir(parents=True)
        with pytest.raises(RunnerError, match="does not exist"):
            workspace._resolve_working_directory("missing")


def test_isolated_workspace_makes_tree_writable(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.runner_service.download_repository_archive",
        lambda *args, **kwargs: CommandResult(
            command="download",
            exit_code=0,
            stdout="",
            stderr="",
            duration_seconds=0.01,
        ),
    )

    def fake_run(command, **kwargs):
        class Completed:
            returncode = 0
            stdout = "done"
            stderr = ""

        return Completed()

    monkeypatch.setattr("app.services.runner_service.subprocess.run", fake_run)

    with IsolatedRunnerWorkspace(
        uuid4(),
        "https://github.com/octo/repo.git",
        settings=Settings(workdir=str(tmp_path)),
    ) as workspace:
        workspace.repo_path.mkdir(parents=True)
        sub = workspace.repo_path / "pkg"
        sub.mkdir()
        (sub / "main.py").write_text("x")
        workspace.checkout("main")
        result = workspace.run("echo ok", working_directory="pkg")
        assert result.exit_code == 0


def test_run_command_timeout(monkeypatch, tmp_path):
    def slow_run(*args, **kwargs):
        import subprocess

        raise subprocess.TimeoutExpired(cmd="sleep", timeout=1)

    monkeypatch.setattr("app.services.runner_service.subprocess.run", slow_run)
    result = run_command("sleep 10", tmp_path, timeout_seconds=1)
    assert result.timed_out is True
    assert result.exit_code is None


def test_run_isolated_command_docker_missing(monkeypatch, tmp_path):
    def missing_docker(*args, **kwargs):
        raise FileNotFoundError("docker")

    monkeypatch.setattr("app.services.runner_service.subprocess.run", missing_docker)
    repo = tmp_path / "repo"
    repo.mkdir()
    result = run_isolated_command("echo", repo, repo_path=repo)
    assert result.exit_code == 127
    assert "Docker CLI" in result.stderr


def test_run_isolated_command_timeout_removes_container(monkeypatch, tmp_path):
    removed = []

    def timeout_run(*args, **kwargs):
        import subprocess

        raise subprocess.TimeoutExpired(cmd="docker", timeout=1)

    def fake_remove(name):
        removed.append(name)

    monkeypatch.setattr("app.services.runner_service.subprocess.run", timeout_run)
    monkeypatch.setattr("app.services.runner_service._remove_container", fake_remove)
    repo = tmp_path / "repo"
    repo.mkdir()
    result = run_isolated_command("echo", repo, repo_path=repo, timeout_seconds=1)
    assert result.timed_out is True
    assert removed


def test_run_isolated_command_rejects_cwd_outside_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(RunnerError, match="inside the repository"):
        run_isolated_command("echo", outside, repo_path=repo)


def test_docker_run_command_rejects_invalid_network(tmp_path):
    from app.services.runner_service import _docker_run_command

    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(RunnerError, match="network policy"):
        _docker_run_command(
            "echo",
            container_name="c",
            repo_root=repo.resolve(),
            container_cwd="/workspace",
            timeout_seconds=5,
            settings=Settings(runner_network="host"),
        )


def test_download_repository_archive_success(monkeypatch, tmp_path):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        data = b"print('hi')"
        info = tarfile.TarInfo(name="repo-root/src/app.py")
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))

    payload = buffer.getvalue()

    class FakeResponse:
        def __init__(self):
            self._offset = 0

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, size=-1):
            if self._offset >= len(payload):
                return b""
            if size < 0:
                chunk = payload[self._offset :]
                self._offset = len(payload)
                return chunk
            chunk = payload[self._offset : self._offset + size]
            self._offset += len(chunk)
            return chunk

    monkeypatch.setattr(
        "app.services.runner_service._opener.open",
        lambda request, timeout=None: FakeResponse(),
    )

    repo_path = tmp_path / "repo"
    root = tmp_path / "root"
    root.mkdir()
    result = download_repository_archive(
        RepositoryRef("octo", "repo", token="tok"),
        "abc",
        repo_path,
        root,
        timeout_seconds=5,
    )
    assert result.exit_code == 0
    assert repo_path.is_dir()
    assert (repo_path / "src" / "app.py").read_text() == "print('hi')"


def test_download_repository_archive_http_error(monkeypatch, tmp_path):
    def raise_http(*args, **kwargs):
        raise urllib.error.HTTPError(
            "https://api.github.com", 404, "Not Found", None, None
        )

    monkeypatch.setattr("app.services.runner_service._opener.open", raise_http)
    repo_path = tmp_path / "repo"
    root = tmp_path / "root"
    root.mkdir()
    result = download_repository_archive(
        RepositoryRef("octo", "repo"),
        "abc",
        repo_path,
        root,
    )
    assert result.exit_code == 1
    assert "HTTP 404" in result.stderr


def test_validate_archive_members_rejects_traversal(tmp_path):
    extract_path = tmp_path / "extract"
    extract_path.mkdir()
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        info = tarfile.TarInfo(name="../escape.txt")
        info.size = 0
        archive.addfile(info, io.BytesIO(b""))
    buffer.seek(0)
    with tarfile.open(fileobj=buffer, mode="r:gz") as archive:
        with pytest.raises(RunnerError, match="unsafe path"):
            _validate_archive_members(archive, extract_path)


def test_command_result_includes_adapter_and_limits():
    result = CommandResult(
        command="echo",
        exit_code=0,
        stdout="",
        stderr="",
        duration_seconds=0.1,
        adapter="isolated",
        resource_limits={"cpu": 1},
    )
    snapshot = result.to_snapshot()
    assert snapshot["runner_adapter"] == "isolated"
    assert snapshot["resource_limits"]["cpu"] == 1
