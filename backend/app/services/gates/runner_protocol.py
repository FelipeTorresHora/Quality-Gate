from pathlib import Path
from typing import Protocol, runtime_checkable

from app.services.runner_service import CommandResult


@runtime_checkable
class Runner(Protocol):
    root: Path
    repo_path: Path
    command_metadata: list[dict]

    def checkout(self, revision: str) -> None: ...

    def run(self, command: str, working_directory: str = ".") -> CommandResult: ...

    def __enter__(self) -> "Runner": ...

    def __exit__(self, exc_type, exc, traceback) -> None: ...
