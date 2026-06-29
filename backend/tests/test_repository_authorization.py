def test_repository_list_requires_authentication(client):
    response = client.get("/api/repositories")

    assert response.status_code == 401


def test_repository_list_is_filtered_to_current_user(
    client,
    reset_database,
    create_user_repo_access,
):
    _user, repository, cookie = create_user_repo_access(is_admin=False)

    response = client.get(
        "/api/repositories",
        cookies={"qg_session": cookie},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [str(repository.id)]


def test_non_admin_cannot_update_quality_gate_config(
    client,
    reset_database,
    create_user_repo_access,
):
    _user, repository, cookie = create_user_repo_access(is_admin=False)

    response = client.put(
        f"/api/repositories/{repository.id}/quality-gate-config",
        cookies={"qg_session": cookie},
        json={"min_total_coverage": 90},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "repository_admin_required"
