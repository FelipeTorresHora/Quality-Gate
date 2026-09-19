import pytest

from app.core.errors import AppError
from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate
from app.services import repository_service


def test_list_repositories_orders_by_full_name(reset_database, db_session):
    db_session.add_all(
        [
            Repository(
                owner="b",
                name="two",
                full_name="org/two",
                default_branch="main",
            ),
            Repository(
                owner="a",
                name="one",
                full_name="org/one",
                default_branch="main",
            ),
        ]
    )
    db_session.commit()
    names = [repo.full_name for repo in repository_service.list_repositories(db_session)]
    assert names == ["org/one", "org/two"]


def test_get_repository_not_found(reset_database, db_session):
    from uuid import uuid4

    with pytest.raises(AppError) as exc:
        repository_service.get_repository(db_session, uuid4())
    assert exc.value.code == "repository_not_found"


def test_create_repository_success(reset_database, db_session):
    payload = RepositoryCreate(
        owner="octo",
        name="new-repo",
        full_name="octo/new-repo",
        default_branch="main",
        github_repo_id=999,
    )
    repo = repository_service.create_repository(db_session, payload)
    assert repo.full_name == "octo/new-repo"
    assert repo.quality_gate_config is not None
    assert repo.coverage_execution_config is not None


def test_create_repository_conflict_by_full_name(reset_database, db_session):
    db_session.add(
        Repository(
            owner="octo",
            name="dup",
            full_name="octo/dup",
            default_branch="main",
        )
    )
    db_session.commit()
    payload = RepositoryCreate(
        owner="octo",
        name="dup",
        full_name="octo/dup",
        default_branch="main",
    )
    with pytest.raises(AppError) as exc:
        repository_service.create_repository(db_session, payload)
    assert exc.value.code == "repository_already_exists"


def test_get_repository_by_full_name(reset_database, db_session):
    repo = Repository(
        owner="octo",
        name="find-me",
        full_name="octo/find-me",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.commit()
    found = repository_service.get_repository_by_full_name(db_session, "octo/find-me")
    assert found.id == repo.id
