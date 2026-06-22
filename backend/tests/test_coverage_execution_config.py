def test_create_repository_creates_default_coverage_execution_config(
    client, reset_database
):
    response = client.post(
        "/api/repositories",
        json={
            "owner": "horinha04",
            "name": "meu-projeto",
            "full_name": "horinha04/meu-projeto",
            "default_branch": "main",
        },
    )
    assert response.status_code == 201
    repository = response.json()

    config_response = client.get(
        f"/api/repositories/{repository['id']}/coverage-execution-config"
    )

    assert config_response.status_code == 200
    config = config_response.json()
    assert config["repository_id"] == repository["id"]
    assert config["language"] == "python"
    assert config["install_command"] == "pip install -r requirements.txt"
    assert config["test_command"] == "pytest --cov=. --cov-report=xml:coverage.xml"
    assert config["report_path"] == "coverage.xml"
    assert config["report_format"] == "cobertura_xml"


def test_update_coverage_execution_config(client, repository):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
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


def test_update_coverage_execution_config_allows_blank_install_command(
    client, repository
):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
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


def test_update_coverage_execution_config_rejects_empty_test_command(
    client, repository
):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
        json={"test_command": "   "},
    )

    assert response.status_code == 422


def test_update_coverage_execution_config_rejects_wrong_report_format(
    client, repository
):
    response = client.put(
        f"/api/repositories/{repository['id']}/coverage-execution-config",
        json={
            "language": "go",
            "report_format": "lcov",
        },
    )

    assert response.status_code == 422


def test_get_coverage_execution_config_missing_repository(client, reset_database):
    response = client.get(
        "/api/repositories/00000000-0000-0000-0000-000000000000/"
        "coverage-execution-config"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "repository_not_found"
