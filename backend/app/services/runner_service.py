from __future__ import annotations

import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.core.config import get_settings

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

    def to_snapshot(self) -> dict:
        return {
            "command": redacted_command(self.command),
            "exit_code": self.exit_code,
            "stdout": redact_secrets(self.stdout[-4000:]),
            "stderr": redact_secrets(self.stderr[-4000:]),
            "duration_seconds": round(self.duration_seconds, 3),
            "timed_out": self.timed_out,
        }


class RunnerWorkspace:
    def __init__(self, analysis_run_id: UUID, repository_url: str) -> None:
        settings = get_settings()
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
    archive_url = (
        f"https://codeload.github.com/{repository.owner}/"
        f"{repository.name}/tar.gz/{revision}"
    )
    command = f"download GitHub archive {archive_url}"
    started = time.monotonic()
    archive_path: Path | None = None
    extract_path: Path | None = None
    try:
        request = urllib.request.Request(
            archive_url,
            headers=_github_archive_headers(repository.token),
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
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


_SECRET_PATTERNS = [
    re.compile(r"x-access-token:[^@\s]+@"),
    re.compile(r"\bghs_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgho_[A-Za-z0-9]{20,}\b"),
    re.compile(
        r"-----BEGIN[ A-Z]*PRIVATE KEY-----.*?-----END[ A-Z]*PRIVATE KEY-----",
        re.S,
    ),
]


def redact_secrets(text: str) -> str:
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("***REDACTED***", text)
    return text


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
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command=command,
            exit_code=None,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
            duration_seconds=time.monotonic() - started,
            timed_out=True,
        )


def _safe_env() -> dict[str, str]:
    safe = {key: os.environ[key] for key in SAFE_ENV_ALLOWLIST if key in os.environ}
    safe.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    return safe
