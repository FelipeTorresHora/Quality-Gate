import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://pr_quality:pr_quality@localhost:5432/pr_quality_test",
)
os.environ.setdefault("GITHUB_TOKEN", "")

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def reset_database():
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL test database is not available: {exc}")
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def repository(client, reset_database):
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
    return response.json()
