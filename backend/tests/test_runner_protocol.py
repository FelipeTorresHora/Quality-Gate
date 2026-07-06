from uuid import uuid4

from app.core.config import Settings
from app.services.gates.runner_protocol import Runner
from app.services.runner_service import (
    IsolatedRunnerWorkspace,
    RunnerError,
    RunnerWorkspace,
    create_runner_workspace,
)
import pytest


def test_runner_workspace_satisfies_runner_protocol():
    workspace = RunnerWorkspace(uuid4(), "https://github.com/octo/repo.git")
    assert isinstance(workspace, Runner)


def test_production_defaults_to_isolated_runner_adapter():
    workspace = create_runner_workspace(
        uuid4(),
        "https://github.com/octo/repo.git",
        settings=Settings(app_env="production"),
    )

    assert isinstance(workspace, IsolatedRunnerWorkspace)
    assert isinstance(workspace, Runner)


def test_production_rejects_local_runner_without_override():
    with pytest.raises(RunnerError, match="local runner adapter is disabled"):
        create_runner_workspace(
            uuid4(),
            "https://github.com/octo/repo.git",
            settings=Settings(app_env="production", runner_adapter="local"),
        )


def test_settings_expose_analysis_total_timeout():
    settings = Settings()
    assert settings.analysis_total_timeout_seconds == 900
    assert settings.command_timeout_seconds <= settings.analysis_total_timeout_seconds
