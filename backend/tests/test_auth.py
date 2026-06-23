from datetime import UTC, datetime, timedelta

from app.models.github_app_installation import GitHubAppInstallation
from app.models.installation_repository import InstallationRepository
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.models.user_session import UserSession
from app.services import session_service


def test_user_session_and_repository_access_models_persist(reset_database, db_session):
    user = User(
        github_user_id=123,
        github_login="octocat",
        name="Octo Cat",
        email=None,
        avatar_url="https://avatars.githubusercontent.com/u/123",
    )
    repository = Repository(
        github_repo_id=456,
        owner="octo-org",
        name="quality-api",
        full_name="octo-org/quality-api",
        default_branch="main",
    )
    installation = GitHubAppInstallation(
        installation_id=789,
        account_id=321,
        account_login="octo-org",
        account_type="Organization",
        repository_selection="selected",
        permissions_json={"contents": "read", "pull_requests": "read"},
        events_json=["pull_request"],
        active=True,
    )
    db_session.add_all([user, repository, installation])
    db_session.flush()
    db_session.add(
        InstallationRepository(
            installation_id=installation.id,
            repository_id=repository.id,
            github_repo_id=456,
            full_name="octo-org/quality-api",
        )
    )
    db_session.add(
        UserRepositoryAccess(
            user_id=user.id,
            repository_id=repository.id,
            installation_id=installation.id,
            permission="admin",
            is_admin=True,
            synced_at=datetime.now(UTC),
        )
    )
    db_session.add(
        UserSession(
            user_id=user.id,
            session_token_hash="session-hash",
            csrf_token_hash="csrf-hash",
            expires_at=datetime.now(UTC) + timedelta(hours=8),
        )
    )
    db_session.commit()

    persisted_installation = db_session.query(GitHubAppInstallation).one()
    persisted_installation_repository = db_session.query(InstallationRepository).one()

    assert persisted_installation.installation_id == 789
    assert persisted_installation.account_login == "octo-org"
    assert persisted_installation.permissions_json == {
        "contents": "read",
        "pull_requests": "read",
    }
    assert persisted_installation_repository.installation_id == persisted_installation.id
    assert persisted_installation_repository.repository_id == repository.id
    assert persisted_installation_repository.full_name == "octo-org/quality-api"
    assert db_session.query(UserSession).count() == 1
    assert db_session.query(UserRepositoryAccess).one().is_admin is True


def test_create_session_returns_raw_cookie_once(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()

    created = session_service.create_session(
        db_session, user, ttl=timedelta(hours=1)
    )

    assert created.cookie_value
    assert created.csrf_token
    assert created.session.session_token_hash != created.cookie_value
    assert (
        session_service.get_user_for_session(db_session, created.cookie_value).id
        == user.id
    )


def test_revoked_session_is_rejected(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(
        db_session, user, ttl=timedelta(hours=1)
    )

    session_service.revoke_session(db_session, created.cookie_value)

    assert session_service.get_user_for_session(db_session, created.cookie_value) is None


def test_expired_session_is_rejected(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(
        db_session, user, ttl=timedelta(seconds=-1)
    )

    assert session_service.get_user_for_session(db_session, created.cookie_value) is None
