def test_create_repository_creates_default_quality_gate_config(client, reset_database):
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
    assert repository["id"]
    assert repository["owner"] == "horinha04"
    assert repository["name"] == "meu-projeto"
    assert repository["full_name"] == "horinha04/meu-projeto"
    assert repository["default_branch"] == "main"
    assert "user_id" not in repository

    config_response = client.get(
        f"/api/repositories/{repository['id']}/quality-gate-config"
    )
    assert config_response.status_code == 200
    config = config_response.json()
    assert config["repository_id"] == repository["id"]
    assert config["min_total_coverage"] == 80
    assert config["max_coverage_drop"] == 0
    assert config["min_changed_files_coverage"] == 75
    assert config["security_fail_on"] == ["critical", "high"]
    assert config["max_function_lines"] == 80
    assert config["max_complexity"] == 10
    assert config["fail_on_new_todo"] is True
    assert config["comment_on_github"] is False
    assert config["publish_github_status"] is False


def test_list_repositories_returns_created_repository(client, repository):
    response = client.get("/api/repositories")

    assert response.status_code == 200
    repositories = response.json()
    assert len(repositories) == 1
    assert repositories[0]["id"] == repository["id"]
    assert repositories[0]["full_name"] == "horinha04/meu-projeto"


def test_create_repository_rejects_duplicate_full_name(client, repository):
    response = client.post(
        "/api/repositories",
        json={
            "owner": "horinha04",
            "name": "meu-projeto",
            "full_name": "horinha04/meu-projeto",
            "default_branch": "main",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "repository_already_exists"
