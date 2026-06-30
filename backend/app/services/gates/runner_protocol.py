from pathlib import Path
from typing import Protocol, runtime_checkable

from app.services.runner_service import CommandResult


@runtime_checkable
class Runner(Protocol):
    repo_path: Path

    def checkout(self, revision: str) -> None: ...

    def run(self, command: str, working_directory: str = ".") -> CommandResult: ...
