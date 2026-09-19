from app.models.coverage_execution_config import CoverageExecutionConfig
from app.models.repository import Repository
from app.models.user import User
from app.services import github_installation_service
from app.services.coverage_execution_config_service import map_github_language


def test_synced_repository_has_default_coverage_execution_config(
    client, repository
):
    config_response = client.get(
        f"/api/repositories/{repository['id']}/coverage-execution-config"
    )

    assert config_response.status_code == 200
    config = config_response.json()
    assert config["repository_id"] == repository["id"]
    assert config["language"] == "python"
    assert config["language_preset_confirmed"] is False
    assert config["working_directory"] == "."
    assert config["install_command"] == "pip install -r requirements.txt"
    assert config["test_command"] == "pytest --cov=. --cov-report=xml:coverage.xml"
    assert config["report_path"] == "coverage.xml"
    assert config["report_format"] == "cobertura_xml"


def test_sync_javascript_repository_applies_npm_lcov_defaults(
    reset_database, db_session
):
    config = _sync_coverage_config(db_session, language="JavaScript")

    assert config.language.value == "javascript"
    assert config.language_preset_confirmed is True
    assert config.install_command == "npm ci"
    assert config.test_command == "npm test -- --coverage"
    assert config.report_path == "coverage/lcov.info"
    assert config.report_format.value == "lcov"


def test_sync_go_repository_applies_go_coverprofile_defaults(
    reset_database, db_session
):
    config = _sync_coverage_config(db_session, language="Go")

    assert config.language.value == "go"
    assert config.language_preset_confirmed is True
    assert config.install_command == "go mod download"
    assert "coverprofile=coverage.out" in config.test_command
    assert config.report_format.value == "go_coverprofile"


def test_sync_unknown_github_language_uses_unconfirmed_python_preset(
    reset_database, db_session
):
    config = _sync_coverage_config(db_session, language="Ruby")

    assert config.language.value == "python"
    assert config.language_preset_confirmed is False
    assert config.install_command == "pip install -r requirements.txt"


def test_map_github_language_known_and_fallback():
    from app.models.enums import CoverageLanguage

    assert map_github_language("JavaScript") == (CoverageLanguage.JAVASCRIPT, True)
    assert map_github_language("TypeScript") == (CoverageLanguage.TYPESCRIPT, True)
    assert map_github_language("Python") == (CoverageLanguage.PYTHON, True)
    assert map_github_language("Go") == (CoverageLanguage.GO, True)
    assert map_github_language("Ruby") == (CoverageLanguage.PYTHON, False)
    assert map_github_language(None) == (CoverageLanguage.PYTHON, False)


def test_update_coverage_execution_config(client, repository, monkeypatch):
    expired = []
    monkeypatch.setattr(
        "app.api.routes_coverage_execution_config.runtime_cache_service.expire_tags",
        lambda tags: expired.extend(tags),
    )

    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
        headers={"X-CSRF-Token": repository["csrf_token"]},
        json={
            "language": "go",
            "install_command": "go mod download",
            "test_command": "go test ./... -coverprofile=coverage.out",
            "report_path": "coverage.out",
            "report_format": "go_coverprofile",
        },
    )

    assert response.status_code == 200
    config = response.json()
    assert config["language"] == "go"
    assert config["install_command"] == "go mod download"
    assert config["test_command"] == "go test ./... -coverprofile=coverage.out"
    assert config["report_path"] == "coverage.out"
    assert config["report_format"] == "go_coverprofile"
    assert f"coverage-config:repo:{repository['id']}" in expired


def test_update_coverage_execution_config_allows_blank_install_command(
    client, repository
):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
        headers={"X-CSRF-Token": repository["csrf_token"]},
        json={
            "language": "javascript",
            "install_command": "",
            "test_command": "npm test -- --coverage",
            "report_path": "coverage/lcov.info",
            "report_format": "lcov",
        },
    )

    assert response.status_code == 200
    assert response.json()["install_command"] == ""


def test_update_coverage_execution_config_accepts_working_directory(
    client, repository
):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
        headers={"X-CSRF-Token": repository["csrf_token"]},
        json={"working_directory": "docker-log-watcher-agent"},
    )

    assert response.status_code == 200
    assert response.json()["working_directory"] == "docker-log-watcher-agent"


def test_update_coverage_execution_config_rejects_empty_test_command(
    client, repository
):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
        headers={"X-CSRF-Token": repository["csrf_token"]},
        json={"test_command": "   "},
    )

    assert response.status_code == 422


def test_update_coverage_execution_config_rejects_wrong_report_format(
    client, repository
):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
        headers={"X-CSRF-Token": repository["csrf_token"]},
        json={
            "language": "go",
            "report_format": "lcov",
        },
    )

    assert response.status_code == 422


def test_get_coverage_execution_config_without_access_is_denied(client, repository):
    response = client.get(
        "/api/repositories/00000000-0000-0000-0000-000000000000/"
        "coverage-execution-config"
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "repository_access_denied"


def test_update_coverage_execution_config_confirms_language_preset(
    client, repository
):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
        headers={"X-CSRF-Token": repository["csrf_token"]},
        json={"language": "javascript"},
    )

    assert response.status_code == 200
    config = response.json()
    assert config["language"] == "javascript"
    assert config["language_preset_confirmed"] is True
    assert config["install_command"] == "npm ci"
    assert config["test_command"] == "npm test -- --coverage"
    assert config["report_path"] == "coverage/lcov.info"
    assert config["report_format"] == "lcov"


def test_update_coverage_execution_config_returns_confirmed_flag(
    client, repository
):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
        headers={"X-CSRF-Token": repository["csrf_token"]},
        json={"working_directory": "."},
    )

    assert response.status_code == 200
    assert response.json()["language_preset_confirmed"] is True


def _sync_coverage_config(db_session, *, language):
    user = User(github_user_id=42, github_login="lang-admin")
    db_session.add(user)
    db_session.commit()
    github_installation_service.sync_installation_payload(
        db_session,
        user=user,
        installation_payload={
            "id": 77,
            "account": {
                "id": 78,
                "login": "octo-org",
                "type": "Organization",
            },
            "repository_selection": "selected",
            "permissions": {},
            "events": ["pull_request"],
        },
        repositories_payload=[
            {
                "id": 79,
                "name": "frontend-app",
                "full_name": "octo-org/frontend-app",
                "owner": {"login": "octo-org"},
                "default_branch": "main",
                "language": language,
                "permissions": {"admin": True, "push": True, "pull": True},
            }
        ],
    )
    repository = (
        db_session.query(Repository).filter_by(full_name="octo-org/frontend-app").one()
    )
    return (
        db_session.query(CoverageExecutionConfig)
        .filter_by(repository_id=repository.id)
        .one()
    )
