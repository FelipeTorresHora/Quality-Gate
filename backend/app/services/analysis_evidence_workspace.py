from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from app.services.runner_service import (
    RunnerError,
    create_runner_workspace,
    repository_clone_url,
)

if TYPE_CHECKING:
    from app.models.analysis_run import AnalysisRun
    from app.models.repository import Repository
    from app.services.gates.runner_protocol import Runner
    from app.services.runner_service import CommandResult

RunnerWorkspace = create_runner_workspace


class PreparedRevision:
    def __init__(self, workspace: "Runner", repo_path: Path) -> None:
        self._workspace = workspace
        self.repo_path = repo_path

    def run(self, command: str, working_directory: str = ".") -> CommandResult:
        previous_repo_path = self._workspace.repo_path
        self._workspace.repo_path = self.repo_path
        try:
            return self._workspace.run(command, working_directory=working_directory)
        finally:
            self._workspace.repo_path = previous_repo_path

    def path_in_working_directory(
        self,
        working_directory: str,
        relative_path: str,
    ) -> Path:
        repo_root = self.repo_path.resolve()
        path = (repo_root / working_directory / relative_path).resolve()
        if not path.is_relative_to(repo_root):
            raise RunnerError("Path must stay inside the repository.")
        return path

    def path_in_repository(self, relative_path: str) -> Path:
        return self.path_in_working_directory(".", relative_path)


class GateExecutionEvidenceWorkspace:
    def __init__(
        self,
        *,
        analysis_run: AnalysisRun,
        repository: Repository,
        repository_token: str | None,
    ) -> None:
        self.analysis_run = analysis_run
        self._workspace = RunnerWorkspace(
            analysis_run.id,
            repository_clone_url(
                repository.owner,
                repository.name,
                repository_token,
            ),
        )
        self._prepared: dict[str, PreparedRevision] = {}

    @property
    def command_metadata(self) -> list[dict]:
        return self._workspace.command_metadata

    def __enter__(self) -> GateExecutionEvidenceWorkspace:
        self._workspace.__enter__()
        (self._workspace.root / "revisions").mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self._workspace.__exit__(exc_type, exc, traceback)

    def metadata_checkpoint(self) -> int:
        return len(self.command_metadata)

    def metadata_since(self, checkpoint: int) -> list[dict]:
        return self.command_metadata[checkpoint:]

    def prepare_head(self) -> PreparedRevision:
        return self.prepare_revision(self.analysis_run.head_sha)

    def prepare_base(self) -> PreparedRevision:
        base_sha = self.analysis_run.pull_request_snapshot_json.get("base_sha")
        if not isinstance(base_sha, str) or not base_sha:
            raise RunnerError("Pull Request base revision is required.")
        return self.prepare_revision(base_sha)

    def prepare_revision(self, revision: str) -> PreparedRevision:
        if revision in self._prepared:
            return self._prepared[revision]

        self._workspace.checkout(revision)
        prepared_path = self._prepared_path(revision)
        if prepared_path.exists():
            shutil.rmtree(prepared_path)
        prepared_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(self._workspace.repo_path), prepared_path)

        prepared = PreparedRevision(self._workspace, prepared_path)
        self._prepared[revision] = prepared
        return prepared

    def _prepared_path(self, revision: str) -> Path:
        digest = hashlib.sha256(revision.encode("utf-8")).hexdigest()[:16]
        return self._workspace.root / "revisions" / digest
