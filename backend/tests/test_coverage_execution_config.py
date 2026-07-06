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
    assert config["working_directory"] == "."
    assert config["install_command"] == "pip install -r requirements.txt"
    assert config["test_command"] == "pytest --cov=. --cov-report=xml:coverage.xml"
    assert config["report_path"] == "coverage.xml"
    assert config["report_format"] == "cobertura_xml"


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
