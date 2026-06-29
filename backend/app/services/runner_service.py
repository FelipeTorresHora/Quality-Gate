from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.core.config import get_settings

SECRET_ENV_PREFIXES = (
    "GITHUB_",
    "OPENAI_",
    "LANGSMITH_",
)
SECRET_ENV_NAMES = {
    "DATABASE_URL",
}


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
            "stdout": self.stdout[-4000:],
            "stderr": self.stderr[-4000:],
            "duration_seconds": round(self.duration_seconds, 3),
            "timed_out": self.timed_out,
        }


class RunnerWorkspace:
    def __init__(self, analysis_run_id: UUID, repository_url: str) -> None:
        settings = get_settings()
        self.root = Path(settings.workdir) / str(analysis_run_id)
        self.repo_path = self.root / "repo"
        self.repository_url = repository_url
        self.command_timeout_seconds = settings.command_timeout_seconds
        self.keep_workdir = settings.keep_workdir
        self.command_metadata: list[dict] = []

    def __enter__(self) -> "RunnerWorkspace":
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        result = run_command(
            f"git clone {self.repository_url} repo",
            self.root,
            timeout_seconds=self.command_timeout_seconds,
        )
        self.command_metadata.append(result.to_snapshot())
        if result.exit_code != 0 or result.timed_out:
            raise RunnerError("Repository clone failed.", result)
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if not self.keep_workdir and self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)

    def checkout(self, revision: str) -> None:
        result = run_command(
            f"git checkout {revision}",
            self.repo_path,
            timeout_seconds=self.command_timeout_seconds,
        )
        self.command_metadata.append(result.to_snapshot())
        if result.exit_code != 0 or result.timed_out:
            raise RunnerError(f"Repository checkout failed for {revision}.", result)

    def run(self, command: str) -> CommandResult:
        result = run_command(
            command,
            self.repo_path,
            timeout_seconds=self.command_timeout_seconds,
        )
        self.command_metadata.append(result.to_snapshot())
        return result


class RunnerError(Exception):
    def __init__(self, message: str, result: CommandResult | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.result = result


def repository_clone_url(
    owner: str,
    name: str,
    token: str | None = None,
) -> str:
    if token:
        return f"https://x-access-token:{token}@github.com/{owner}/{name}.git"
    return f"https://github.com/{owner}/{name}.git"


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
    safe: dict[str, str] = {}
    for key, value in os.environ.items():
        if key in SECRET_ENV_NAMES:
            continue
        if any(key.startswith(prefix) for prefix in SECRET_ENV_PREFIXES):
            continue
        safe[key] = value
    return safe
