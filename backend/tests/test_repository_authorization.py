from datetime import UTC, datetime

from app.models.github_app_installation import GitHubAppInstallation
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.services import session_service


def create_user_repo_access(db_session, *, is_admin: bool):
    user = User(
        github_user_id=10 if is_admin else 11,
        github_login="admin" if is_admin else "viewer",
    )
    repository = Repository(
        github_repo_id=200,
        owner="octo-org",
        name="quality-api",
        full_name="octo-org/quality-api",
        default_branch="main",
    )
    installation = GitHubAppInstallation(
        installation_id=300,
        account_id=400,
        account_login="octo-org",
        account_type="Organization",
        permissions_json={},
        events_json=[],
        active=True,
    )
    db_session.add_all([user, repository, installation])
    db_session.flush()
    db_session.add(
        UserRepositoryAccess(
            user_id=user.id,
            repository_id=repository.id,
            installation_id=installation.id,
            permission="admin" if is_admin else "pull",
            is_admin=is_admin,
            synced_at=datetime.now(UTC),
        )
    )
    db_session.commit()
    created = session_service.create_session(db_session, user)
    return user, repository, created.cookie_value


def test_repository_list_requires_authentication(client):
    response = client.get("/api/repositories")

    assert response.status_code == 401


def test_repository_list_is_filtered_to_current_user(
    client,
    reset_database,
    db_session,
):
    _user, repository, cookie = create_user_repo_access(
        db_session,
        is_admin=False,
    )

    response = client.get(
        "/api/repositories",
        cookies={"qg_session": cookie},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [str(repository.id)]


def test_non_admin_cannot_update_quality_gate_config(
    client,
    reset_database,
    db_session,
):
    _user, repository, cookie = create_user_repo_access(
        db_session,
        is_admin=False,
    )

    response = client.put(
        f"/api/repositories/{repository.id}/quality-gate-config",
        cookies={"qg_session": cookie},
        json={"min_total_coverage": 90},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "repository_admin_required"
