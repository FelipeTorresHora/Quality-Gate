from uuid import uuid4

from app.core.config import Settings
from app.services.gates.runner_protocol import Runner
from app.services.runner_service import RunnerWorkspace


def test_runner_workspace_satisfies_runner_protocol():
    workspace = RunnerWorkspace(uuid4(), "https://github.com/octo/repo.git")
    assert isinstance(workspace, Runner)


def test_settings_expose_analysis_total_timeout():
    settings = Settings()
    assert settings.analysis_total_timeout_seconds == 900
    assert settings.command_timeout_seconds <= settings.analysis_total_timeout_seconds
