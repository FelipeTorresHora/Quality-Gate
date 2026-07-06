from __future__ import annotations

import os
import re
import shutil
import shlex
import stat
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from app.core.config import get_settings
from app.services.evidence_redaction_service import redact_text

SAFE_ENV_ALLOWLIST = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "TZ",
    "TMPDIR",
    "SHELL",
    "GOPATH",
    "GOCACHE",
    "GOMODCACHE",
    "NODE_ENV",
    "PYTHONUNBUFFERED",
    "PYTHONDONTWRITEBYTECODE",
)


@dataclass
class CommandResult:
    command: str
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    adapter: str | None = None
    resource_limits: dict[str, str | int | float] | None = None

    def to_snapshot(self) -> dict:
        snapshot = {
            "command": redacted_command(self.command),
            "exit_code": self.exit_code,
            "stdout": redact_text(self.stdout[-4000:]),
            "stderr": redact_text(self.stderr[-4000:]),
            "duration_seconds": round(self.duration_seconds, 3),
            "timed_out": self.timed_out,
        }
        if self.adapter:
            snapshot["runner_adapter"] = self.adapter
        if self.resource_limits:
            snapshot["resource_limits"] = self.resource_limits
        return snapshot


class RunnerWorkspace:
    def __init__(
        self,
        analysis_run_id: UUID,
        repository_url: str,
        *,
        settings=None,
    ) -> None:
        settings = settings or get_settings()
        self.root = Path(settings.workdir) / str(analysis_run_id)
        self.repo_path = self.root / "repo"
        self.repository_url = repository_url
        self.repository_ref = parse_repository_url(repository_url)
        self.command_timeout_seconds = settings.command_timeout_seconds
        self.keep_workdir = settings.keep_workdir
        self.command_metadata: list[dict] = []

    def __enter__(self) -> "RunnerWorkspace":
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if not self.keep_workdir and self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)

    def checkout(self, revision: str) -> None:
        result = download_repository_archive(
            self.repository_ref,
            revision,
            self.repo_path,
            self.root,
            timeout_seconds=self.command_timeout_seconds,
        )
        self.command_metadata.append(result.to_snapshot())
        if result.exit_code != 0 or result.timed_out:
            raise RunnerError(f"Repository checkout failed for {revision}.", result)

    def run(self, command: str, working_directory: str = ".") -> CommandResult:
        cwd = self._resolve_working_directory(working_directory)
        result = run_command(
            command,
            cwd,
            timeout_seconds=self.command_timeout_seconds,
        )
        self.command_metadata.append(result.to_snapshot())
        return result

    def _resolve_working_directory(self, working_directory: str) -> Path:
        repo_root = self.repo_path.resolve()
        cwd = (repo_root / working_directory).resolve()
        if not cwd.is_relative_to(repo_root):
            raise RunnerError("Working directory must stay inside the repository.")
        if not cwd.exists() or not cwd.is_dir():
            raise RunnerError(f"Working directory does not exist: {working_directory}.")
        return cwd


class IsolatedRunnerWorkspace:
    def __init__(
        self,
        analysis_run_id: UUID,
        repository_url: str,
        *,
        settings=None,
    ) -> None:
        self._settings = settings or get_settings()
        self.root = Path(self._settings.workdir) / str(analysis_run_id)
        self.repo_path = self.root / "repo"
        self.repository_url = repository_url
        self.repository_ref = parse_repository_url(repository_url)
        self.command_timeout_seconds = self._settings.command_timeout_seconds
        self.keep_workdir = self._settings.keep_workdir
        self.command_metadata: list[dict] = []

    def __enter__(self) -> "IsolatedRunnerWorkspace":
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if not self.keep_workdir and self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)

    def checkout(self, revision: str) -> None:
        result = download_repository_archive(
            self.repository_ref,
            revision,
            self.repo_path,
            self.root,
            timeout_seconds=self.command_timeout_seconds,
        )
        self.command_metadata.append(result.to_snapshot())
        if result.exit_code != 0 or result.timed_out:
            raise RunnerError(f"Repository checkout failed for {revision}.", result)
        _make_workspace_writable(self.repo_path)

    def run(self, command: str, working_directory: str = ".") -> CommandResult:
        cwd = self._resolve_working_directory(working_directory)
        result = run_isolated_command(
            command,
            cwd,
            repo_path=self.repo_path,
            timeout_seconds=self.command_timeout_seconds,
            settings=self._settings,
        )
        self.command_metadata.append(result.to_snapshot())
        return result

    def _resolve_working_directory(self, working_directory: str) -> Path:
        repo_root = self.repo_path.resolve()
        cwd = (repo_root / working_directory).resolve()
        if not cwd.is_relative_to(repo_root):
            raise RunnerError("Working directory must stay inside the repository.")
        if not cwd.exists() or not cwd.is_dir():
            raise RunnerError(f"Working directory does not exist: {working_directory}.")
        return cwd


class RunnerError(Exception):
    def __init__(self, message: str, result: CommandResult | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.result = result


@dataclass(frozen=True)
class RepositoryRef:
    owner: str
    name: str
    token: str | None = None


def repository_clone_url(
    owner: str,
    name: str,
    token: str | None = None,
) -> str:
    if token:
        return f"https://x-access-token:{token}@github.com/{owner}/{name}.git"
    return f"https://github.com/{owner}/{name}.git"


def create_runner_workspace(
    analysis_run_id: UUID,
    repository_url: str,
    *,
    settings=None,
) -> RunnerWorkspace | IsolatedRunnerWorkspace:
    settings = settings or get_settings()
    adapter = (settings.runner_adapter or _default_runner_adapter(settings)).lower()
    if adapter == "local":
        if (
            settings.app_env == "production"
            and not settings.allow_local_runner_in_production
        ):
            raise RunnerError(
                "The local runner adapter is disabled in production without an explicit override."
            )
        return RunnerWorkspace(analysis_run_id, repository_url, settings=settings)
    if adapter in {"isolated", "container"}:
        return IsolatedRunnerWorkspace(analysis_run_id, repository_url, settings=settings)
    raise RunnerError(f"Unsupported runner adapter: {adapter}.")


def _default_runner_adapter(settings) -> str:
    return "isolated" if settings.app_env == "production" else "local"


def parse_repository_url(repository_url: str) -> RepositoryRef:
    parsed = urllib.parse.urlparse(repository_url)
    if parsed.hostname != "github.com":
        raise RunnerError("Only GitHub repository URLs are supported.")
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise RunnerError("GitHub repository URL is invalid.")
    token = None
    if parsed.username == "x-access-token" and parsed.password:
        token = urllib.parse.unquote(parsed.password)
    return RepositoryRef(owner=parts[0], name=parts[1], token=token)


def download_repository_archive(
    repository: RepositoryRef,
    revision: str,
    repo_path: Path,
    root: Path,
    *,
    timeout_seconds: int | None = None,
) -> CommandResult:
    timeout = timeout_seconds or get_settings().command_timeout_seconds
    archive_url = _archive_url(repository.owner, repository.name, revision)
    command = f"download GitHub archive {archive_url}"
    started = time.monotonic()
    archive_path: Path | None = None
    extract_path: Path | None = None
    try:
        request = urllib.request.Request(
            archive_url,
            headers=_github_archive_headers(repository.token),
        )
        with _opener.open(request, timeout=timeout) as response:
            with tempfile.NamedTemporaryFile(
                suffix=".tar.gz",
                dir=root,
                delete=False,
            ) as archive_file:
                archive_path = Path(archive_file.name)
                shutil.copyfileobj(response, archive_file)

        extract_path = root / "extract"
        if extract_path.exists():
            shutil.rmtree(extract_path)
        extract_path.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "r:gz") as archive:
            _validate_archive_members(archive, extract_path)
            archive.extractall(extract_path, filter="data")

        children = list(extract_path.iterdir())
        if len(children) != 1 or not children[0].is_dir():
            raise RunnerError("GitHub archive layout was not recognized.")
        if repo_path.exists():
            shutil.rmtree(repo_path)
        shutil.move(str(children[0]), repo_path)
        return CommandResult(
            command=command,
            exit_code=0,
            stdout="GitHub archive downloaded and extracted.",
            stderr="",
            duration_seconds=time.monotonic() - started,
        )
    except urllib.error.HTTPError as exc:
        return CommandResult(
            command=command,
            exit_code=1,
            stdout="",
            stderr=f"GitHub archive download failed with HTTP {exc.code}: {exc.reason}",
            duration_seconds=time.monotonic() - started,
        )
    except (
        OSError,
        tarfile.TarError,
        urllib.error.URLError,
        TimeoutError,
        RunnerError,
    ) as exc:
        return CommandResult(
            command=command,
            exit_code=1,
            stdout="",
            stderr=str(exc),
            duration_seconds=time.monotonic() - started,
        )
    finally:
        if archive_path is not None:
            archive_path.unlink(missing_ok=True)
        if extract_path is not None and extract_path.exists():
            shutil.rmtree(extract_path, ignore_errors=True)


def _archive_url(owner: str, name: str, revision: str) -> str:
    return f"https://api.github.com/repos/{owner}/{name}/tarball/{revision}"


class _NoAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            new.headers.pop("Authorization", None)
        return new


_opener = urllib.request.build_opener(_NoAuthOnRedirect)


def _github_archive_headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "quality-gate-runner",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _validate_archive_members(archive: tarfile.TarFile, extract_path: Path) -> None:
    extract_root = extract_path.resolve()
    for member in archive.getmembers():
        target = (extract_root / member.name).resolve()
        if not target.is_relative_to(extract_root):
            raise RunnerError("GitHub archive contains an unsafe path.")


def redacted_command(command: str) -> str:
    return re.sub(
        r"x-access-token:[^@]+@",
        "x-access-token:***@",
        command,
    )


def run_command(
    command: str,
    cwd: str | Path,
    *,
    timeout_seconds: int | None = None,
) -> CommandResult:
    timeout = timeout_seconds or get_settings().command_timeout_seconds
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=Path(cwd),
            env=_safe_env(),
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return CommandResult(
            command=command,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=time.monotonic() - started,
            timed_out=False,
            adapter="local",
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command=command,
            exit_code=None,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
            duration_seconds=time.monotonic() - started,
            timed_out=True,
            adapter="local",
        )


def run_isolated_command(
    command: str,
    cwd: str | Path,
    *,
    repo_path: Path,
    timeout_seconds: int | None = None,
    settings=None,
) -> CommandResult:
    settings = settings or get_settings()
    timeout = timeout_seconds or settings.command_timeout_seconds
    repo_root = repo_path.resolve()
    host_cwd = Path(cwd).resolve()
    if not host_cwd.is_relative_to(repo_root):
        raise RunnerError("Working directory must stay inside the repository.")
    container_cwd = "/workspace"
    relative_cwd = host_cwd.relative_to(repo_root).as_posix()
    if relative_cwd != ".":
        container_cwd = f"{container_cwd}/{relative_cwd}"

    resource_limits = _runner_resource_limits(settings)
    container_name = f"quality-gate-runner-{uuid4().hex}"
    docker_command = _docker_run_command(
        command,
        container_name=container_name,
        repo_root=repo_root,
        container_cwd=container_cwd,
        timeout_seconds=timeout,
        settings=settings,
    )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            docker_command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 10,
        )
        timed_out = completed.returncode == 124
        return CommandResult(
            command=command,
            exit_code=None if timed_out else completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=time.monotonic() - started,
            timed_out=timed_out,
            adapter="isolated",
            resource_limits=resource_limits,
        )
    except FileNotFoundError:
        return CommandResult(
            command=command,
            exit_code=127,
            stdout="",
            stderr="Docker CLI is required for the isolated runner adapter.",
            duration_seconds=time.monotonic() - started,
            timed_out=False,
            adapter="isolated",
            resource_limits=resource_limits,
        )
    except subprocess.TimeoutExpired as exc:
        _remove_container(container_name)
        return CommandResult(
            command=command,
            exit_code=None,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
            duration_seconds=time.monotonic() - started,
            timed_out=True,
            adapter="isolated",
            resource_limits=resource_limits,
        )


def _docker_run_command(
    command: str,
    *,
    container_name: str,
    repo_root: Path,
    container_cwd: str,
    timeout_seconds: int,
    settings,
) -> list[str]:
    if settings.runner_network not in {"none", "bridge"}:
        raise RunnerError("Runner network policy must be 'none' or 'bridge'.")

    docker_command = [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--network",
        settings.runner_network,
        "--cpus",
        str(settings.runner_cpu_limit),
        "--memory",
        settings.runner_memory_limit,
        "--pids-limit",
        str(settings.runner_pids_limit),
        "--user",
        "65532:65532",
        "--workdir",
        container_cwd,
        "--mount",
        f"type=bind,source={repo_root},target=/workspace",
        "--tmpfs",
        f"/tmp:rw,nosuid,nodev,size={settings.runner_tmpfs_size}",
    ]
    for key, value in _safe_env().items():
        docker_command.extend(["--env", f"{key}={value}"])
    docker_command.extend(
        [
            settings.runner_container_image,
            "sh",
            "-lc",
            f"timeout {int(timeout_seconds)} sh -lc {shlex.quote(command)}",
        ]
    )
    return docker_command


def _runner_resource_limits(settings) -> dict[str, str | int | float]:
    return {
        "network": settings.runner_network,
        "cpu": settings.runner_cpu_limit,
        "memory": settings.runner_memory_limit,
        "pids": settings.runner_pids_limit,
        "tmpfs": settings.runner_tmpfs_size,
        "timeout_seconds": settings.command_timeout_seconds,
    }


def _remove_container(container_name: str) -> None:
    try:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return


def _make_workspace_writable(path: Path) -> None:
    for item in [path, *path.rglob("*")]:
        try:
            mode = item.stat().st_mode
            if item.is_dir():
                item.chmod(mode | stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            else:
                item.chmod(
                    mode
                    | stat.S_IRUSR
                    | stat.S_IWUSR
                    | stat.S_IRGRP
                    | stat.S_IWGRP
                    | stat.S_IROTH
                    | stat.S_IWOTH
                )
        except OSError:
            continue


def _safe_env() -> dict[str, str]:
    safe = {key: os.environ[key] for key in SAFE_ENV_ALLOWLIST if key in os.environ}
    safe.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    return safe
