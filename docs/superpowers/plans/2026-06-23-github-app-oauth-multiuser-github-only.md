# GitHub App OAuth Multi-User GitHub-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the product usable only through GitHub App/OAuth multi-user flows, with real automatic/manual Pull Request analysis and no mock analysis surface.

**Architecture:** Use a single GitHub App for user OAuth login and repository installation access. Store local HTTP-only sessions, track GitHub App installations, keep Repository policy shared per repository, and authorize user actions through cached GitHub repository access. Use installation tokens for repository API calls, cloning, webhook analysis, and GitHub publication.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic, httpx, PyJWT/cryptography, React, TypeScript, Vite, GitHub REST API.

---

## Implementation Notes

Run backend tests from `C:\Users\Felipe\Documents\quality-gate\backend` with:

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

Run frontend verification from `C:\Users\Felipe\Documents\quality-gate\frontend` with:

```powershell
npm run build
```

The current branch has unrelated in-progress AI review/GitHub publication code. Do not revert it. When staging task commits, stage only files touched by the task.

## File Structure

Create backend auth/session files:

- `backend/app/models/user_session.py`: server-side dashboard sessions.
- `backend/app/models/github_app_installation.py`: GitHub App installation metadata.
- `backend/app/models/installation_repository.py`: repositories granted to an installation.
- `backend/app/models/user_repository_access.py`: cached current user access/admin state.
- `backend/app/schemas/auth.py`: `/api/auth/me` response DTOs.
- `backend/app/schemas/github_installation.py`: installation sync DTOs.
- `backend/app/services/session_service.py`: session token hashing, cookie values, lookup, revocation.
- `backend/app/services/github_app_auth_service.py`: GitHub App JWT and installation token generation.
- `backend/app/services/github_oauth_service.py`: GitHub App OAuth user login flow.
- `backend/app/services/github_installation_service.py`: installation sync, repository access checks, admin checks.
- `backend/app/api/deps.py`: auth dependencies such as `get_current_user`.
- `backend/app/api/routes_auth.py`: login, callback, me, logout.
- `backend/app/api/routes_github_installations.py`: installation callback and sync endpoints.

Modify existing backend files:

- `backend/app/main.py`: include auth and installation routers.
- `backend/app/db/base.py` and `backend/app/models/__init__.py`: import new models.
- `backend/app/core/config.py`: GitHub App, session, encryption, callback settings.
- `backend/app/models/user.py`: GitHub identity fields.
- `backend/app/models/github_connection.py`: replace legacy token storage with GitHub App user authorization metadata.
- `backend/app/models/enums.py`: remove product use of `mock`.
- `backend/app/api/routes_repositories.py`: remove create endpoints, add auth/access dependencies, add manual PR analyze endpoint.
- `backend/app/api/routes_quality_gate.py`: require access for reads and Repository Admin for writes.
- `backend/app/api/routes_coverage_execution_config.py`: require access for reads and Repository Admin for writes.
- `backend/app/api/routes_analysis.py`: remove mock route and require access/admin for detail/publication.
- `backend/app/api/routes_github_webhooks.py`: use `BackgroundTasks`.
- `backend/app/services/github_service.py`: use token-injected client and installation token flows.
- `backend/app/services/github_webhook_service.py`: handle GitHub App installation events and automatic PR analysis.
- `backend/app/services/analysis_service.py`: remove mock scenarios and add live PR analysis creation helpers.
- `backend/app/services/analysis_execution_service.py`: execute with installation token clone support.
- `backend/app/services/runner_service.py`: authenticated clone without token leakage.
- `backend/app/services/github_publication_service.py`: use installation token, not global `GITHUB_TOKEN`.
- `backend/app/schemas/analysis.py`: remove `MockScenario` and `MockAnalysisRunCreate`.
- `backend/app/schemas/github.py`: keep live GitHub PR/context DTOs and ensure they expose the fields needed by manual analysis.
- `backend/requirements.txt`: add `PyJWT` and `cryptography` if not already present.
- `.env.example`, `README.md`: document GitHub App/OAuth setup and remove mock docs.

Create/modify migrations:

- `backend/alembic/versions/20260623_0005_github_app_oauth_multiuser.py`: new auth/install/access tables and user/github connection changes.
- `backend/alembic/versions/20260623_0006_remove_mock_analysis.py`: delete mock runs and remove mock trigger enum value.

Create/modify backend tests:

- `backend/tests/test_auth.py`
- `backend/tests/test_github_app_auth.py`
- `backend/tests/test_github_installations.py`
- `backend/tests/test_repository_authorization.py`
- `backend/tests/test_manual_pr_analysis.py`
- `backend/tests/test_github_webhooks.py`
- `backend/tests/test_repositories.py`
- `backend/tests/test_analysis_runs.py`
- `backend/tests/test_github_publication.py`

Modify frontend files:

- `frontend/src/types/api.ts`: auth, installation, repository admin/access DTOs; remove mock types.
- `frontend/src/api/client.ts`: auth/install/manual analyze methods; remove mock create method.
- `frontend/src/App.tsx`: authenticated route shell.
- `frontend/src/pages/RepositoriesPage.tsx`: remove manual creation; show install/manage GitHub App states.
- `frontend/src/pages/RepositoryPullRequestsPage.tsx`: remove mock panel; add Analyze action for live PRs.
- `frontend/src/pages/RepositoryQualityGateConfigPage.tsx`: read-only for non-admin.
- `frontend/src/pages/AnalysisDetailPage.tsx`: publish button gated by admin.
- `frontend/src/pages/DashboardPage.tsx`: remove mock language.
- `frontend/src/components/AuthGate.tsx`: create auth-loading/login wrapper.

---

### Task 1: Add Auth And Installation Persistence

**Files:**
- Create: `backend/app/models/user_session.py`
- Create: `backend/app/models/github_app_installation.py`
- Create: `backend/app/models/installation_repository.py`
- Create: `backend/app/models/user_repository_access.py`
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/models/github_connection.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/db/base.py`
- Create: `backend/alembic/versions/20260623_0005_github_app_oauth_multiuser.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing model persistence tests**

Add this to `backend/tests/test_auth.py`:

```python
from datetime import UTC, datetime, timedelta

from app.models.github_app_installation import GitHubAppInstallation
from app.models.installation_repository import InstallationRepository
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.models.user_session import UserSession


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

    assert db_session.query(UserSession).count() == 1
    assert db_session.query(UserRepositoryAccess).one().is_admin is True
```

Also add a `db_session` fixture to `backend/tests/conftest.py` if it does not exist:

```python
@pytest.fixture
def db_session(reset_database):
    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

- [ ] **Step 2: Run the model test and verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py::test_user_session_and_repository_access_models_persist -v
```

Expected: FAIL with an import error for one of the new model modules.

- [ ] **Step 3: Create the new SQLAlchemy models**

Create `backend/app/models/user_session.py`:

```python
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UserSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_sessions"

    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    csrf_token_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
```

Create `backend/app/models/github_app_installation.py`:

```python
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GitHubAppInstallation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "github_app_installations"

    installation_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    account_login: Mapped[str] = mapped_column(Text, nullable=False)
    account_type: Mapped[str] = mapped_column(Text, nullable=False)
    repository_selection: Mapped[str | None] = mapped_column(Text, nullable=True)
    permissions_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    events_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    repositories: Mapped[list["InstallationRepository"]] = relationship(
        back_populates="installation",
        cascade="all, delete-orphan",
    )
    user_access: Mapped[list["UserRepositoryAccess"]] = relationship(
        back_populates="installation",
        cascade="all, delete-orphan",
    )
```

Create `backend/app/models/installation_repository.py`:

```python
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InstallationRepository(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "installation_repositories"
    __table_args__ = (
        UniqueConstraint("installation_id", "repository_id", name="uq_installation_repository"),
    )

    installation_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("github_app_installations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repository_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_repo_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)

    installation: Mapped["GitHubAppInstallation"] = relationship(back_populates="repositories")
    repository: Mapped["Repository"] = relationship()
```

Create `backend/app/models/user_repository_access.py`:

```python
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UserRepositoryAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_repository_access"
    __table_args__ = (
        UniqueConstraint("user_id", "repository_id", name="uq_user_repository_access"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repository_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    installation_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("github_app_installations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="repository_access")
    repository: Mapped["Repository"] = relationship()
    installation: Mapped["GitHubAppInstallation"] = relationship(back_populates="user_access")
```

- [ ] **Step 4: Update existing models and metadata imports**

Modify `backend/app/models/user.py` to:

```python
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    github_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    github_login: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    github_connections: Mapped[list["GitHubConnection"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    repository_access: Mapped[list["UserRepositoryAccess"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
```

Modify `backend/app/models/github_connection.py` to:

```python
from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GitHubConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "github_connections"

    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    github_login: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="github_connections")
```

Modify `backend/app/db/base.py` to import the new modules:

```python
from app.models import github_app_installation  # noqa: E402,F401
from app.models import installation_repository  # noqa: E402,F401
from app.models import user_repository_access  # noqa: E402,F401
from app.models import user_session  # noqa: E402,F401
```

Modify `backend/app/models/__init__.py` to import new model classes if this file currently exports model classes.

- [ ] **Step 5: Add Alembic migration**

Create `backend/alembic/versions/20260623_0005_github_app_oauth_multiuser.py` with:

```python
"""github app oauth multiuser

Revision ID: 20260623_0005
Revises: 20260622_0004
Create Date: 2026-06-23
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260623_0005"
down_revision: str | None = "20260622_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("github_user_id", sa.BigInteger(), nullable=True))
    op.add_column("users", sa.Column("github_login", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=2048), nullable=True))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("users", "name", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=True)
    op.create_index("ix_users_github_user_id", "users", ["github_user_id"], unique=True)
    op.create_index("ix_users_github_login", "users", ["github_login"], unique=True)

    op.add_column("github_connections", sa.Column("github_user_id", sa.BigInteger(), nullable=True))
    op.add_column("github_connections", sa.Column("github_login", sa.String(length=255), nullable=True))
    op.add_column("github_connections", sa.Column("refresh_token_encrypted", sa.Text(), nullable=True))
    op.add_column("github_connections", sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("github_connections", sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("github_connections", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("github_connections", "access_token_encrypted", existing_type=sa.String(length=2048), type_=sa.Text(), nullable=True)
    op.create_index("ix_github_connections_user_id", "github_connections", ["user_id"])
    op.create_index("ix_github_connections_github_user_id", "github_connections", ["github_user_id"])

    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_token_hash", sa.Text(), nullable=False),
        sa.Column("csrf_token_hash", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token_hash"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])

    op.create_table(
        "github_app_installations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("installation_id", sa.BigInteger(), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("account_login", sa.Text(), nullable=False),
        sa.Column("account_type", sa.Text(), nullable=False),
        sa.Column("repository_selection", sa.Text(), nullable=True),
        sa.Column("permissions_json", postgresql.JSONB(), nullable=False),
        sa.Column("events_json", postgresql.JSONB(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("installation_id"),
    )
    op.create_index("ix_github_app_installations_installation_id", "github_app_installations", ["installation_id"], unique=True)
    op.create_index("ix_github_app_installations_account_id", "github_app_installations", ["account_id"])

    op.create_table(
        "installation_repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("installation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_repo_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["installation_id"], ["github_app_installations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("installation_id", "repository_id", name="uq_installation_repository"),
    )
    op.create_index("ix_installation_repositories_installation_id", "installation_repositories", ["installation_id"])
    op.create_index("ix_installation_repositories_repository_id", "installation_repositories", ["repository_id"])
    op.create_index("ix_installation_repositories_github_repo_id", "installation_repositories", ["github_repo_id"])

    op.create_table(
        "user_repository_access",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("installation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission", sa.Text(), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["installation_id"], ["github_app_installations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "repository_id", name="uq_user_repository_access"),
    )
    op.create_index("ix_user_repository_access_user_id", "user_repository_access", ["user_id"])
    op.create_index("ix_user_repository_access_repository_id", "user_repository_access", ["repository_id"])
    op.create_index("ix_user_repository_access_installation_id", "user_repository_access", ["installation_id"])


def downgrade() -> None:
    op.drop_table("user_repository_access")
    op.drop_table("installation_repositories")
    op.drop_table("github_app_installations")
    op.drop_table("user_sessions")
    op.drop_index("ix_github_connections_github_user_id", table_name="github_connections")
    op.drop_index("ix_github_connections_user_id", table_name="github_connections")
    op.alter_column("github_connections", "access_token_encrypted", existing_type=sa.Text(), type_=sa.String(length=2048), nullable=False)
    op.drop_column("github_connections", "revoked_at")
    op.drop_column("github_connections", "refresh_token_expires_at")
    op.drop_column("github_connections", "access_token_expires_at")
    op.drop_column("github_connections", "refresh_token_encrypted")
    op.drop_column("github_connections", "github_login")
    op.drop_column("github_connections", "github_user_id")
    op.drop_index("ix_users_github_login", table_name="users")
    op.drop_index("ix_users_github_user_id", table_name="users")
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("users", "name", existing_type=sa.String(length=255), nullable=False)
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "github_login")
    op.drop_column("users", "github_user_id")
```

- [ ] **Step 6: Run model test and migration smoke**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py::test_user_session_and_repository_access_models_persist -v
```

Expected: PASS when PostgreSQL test DB is available; SKIP only if the configured PostgreSQL test database is unavailable.

- [ ] **Step 7: Commit**

```powershell
git add backend/app/models backend/app/db/base.py backend/alembic/versions/20260623_0005_github_app_oauth_multiuser.py backend/tests/conftest.py backend/tests/test_auth.py
git commit -m "feat: add github app multiuser persistence"
```

---

### Task 2: Add Settings, Session Service, And Auth Dependencies

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/app/services/session_service.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/schemas/auth.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing session service tests**

Append to `backend/tests/test_auth.py`:

```python
from datetime import UTC, datetime, timedelta

from app.services import session_service


def test_create_session_returns_raw_cookie_once(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()

    created = session_service.create_session(db_session, user, ttl=timedelta(hours=1))

    assert created.cookie_value
    assert created.csrf_token
    assert created.session.session_token_hash != created.cookie_value
    assert session_service.get_user_for_session(db_session, created.cookie_value).id == user.id


def test_revoked_session_is_rejected(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(db_session, user, ttl=timedelta(hours=1))

    session_service.revoke_session(db_session, created.cookie_value)

    assert session_service.get_user_for_session(db_session, created.cookie_value) is None


def test_expired_session_is_rejected(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()
    created = session_service.create_session(db_session, user, ttl=timedelta(seconds=-1))

    assert session_service.get_user_for_session(db_session, created.cookie_value) is None
```

- [ ] **Step 2: Run session tests and verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py::test_create_session_returns_raw_cookie_once tests\test_auth.py::test_revoked_session_is_rejected tests\test_auth.py::test_expired_session_is_rejected -v
```

Expected: FAIL because `session_service` does not exist.

- [ ] **Step 3: Add config settings**

Modify `backend/app/core/config.py` by adding fields to `Settings`:

```python
github_app_id: str | None = None
github_app_client_id: str | None = None
github_app_client_secret: str | None = None
github_app_private_key: str | None = None
github_app_private_key_path: str | None = None
github_app_slug: str | None = None
github_api_version: str = "2022-11-28"
session_secret: str = "development-session-secret"
session_cookie_name: str = "qg_session"
session_cookie_secure: bool = False
token_encryption_key: str | None = None
auth_callback_url: str = "http://localhost:8000/api/auth/github/callback"
```

- [ ] **Step 4: Implement session service**

Create `backend/app/services/session_service.py`:

```python
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.models.user_session import UserSession


@dataclass
class CreatedSession:
    session: UserSession
    cookie_value: str
    csrf_token: str


def _hash_token(value: str) -> str:
    secret = get_settings().session_secret.encode("utf-8")
    return hmac.new(secret, value.encode("utf-8"), hashlib.sha256).hexdigest()


def create_session(
    db: Session,
    user: User,
    *,
    ttl: timedelta = timedelta(hours=8),
) -> CreatedSession:
    cookie_value = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)
    session = UserSession(
        user_id=user.id,
        session_token_hash=_hash_token(cookie_value),
        csrf_token_hash=_hash_token(csrf_token),
        expires_at=datetime.now(UTC) + ttl,
        last_seen_at=datetime.now(UTC),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return CreatedSession(session=session, cookie_value=cookie_value, csrf_token=csrf_token)


def get_user_for_session(db: Session, cookie_value: str | None) -> User | None:
    if not cookie_value:
        return None
    session = db.scalar(
        select(UserSession).where(
            UserSession.session_token_hash == _hash_token(cookie_value)
        )
    )
    if session is None:
        return None
    if session.revoked_at is not None or session.expires_at <= datetime.now(UTC):
        return None
    session.last_seen_at = datetime.now(UTC)
    db.commit()
    return db.get(User, session.user_id)


def revoke_session(db: Session, cookie_value: str | None) -> None:
    if not cookie_value:
        return
    session = db.scalar(
        select(UserSession).where(
            UserSession.session_token_hash == _hash_token(cookie_value)
        )
    )
    if session is None:
        return
    session.revoked_at = datetime.now(UTC)
    db.commit()
```

- [ ] **Step 5: Add auth schemas and dependencies**

Create `backend/app/schemas/auth.py`:

```python
from uuid import UUID

from pydantic import BaseModel


class CurrentUserRead(BaseModel):
    id: UUID
    github_user_id: int
    github_login: str
    name: str | None = None
    avatar_url: str | None = None
    has_github_connection: bool
```

Create `backend/app/api/deps.py`:

```python
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.services import session_service


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    cookie_name = get_settings().session_cookie_name
    cookie_value = request.cookies.get(cookie_name)
    user = session_service.get_user_for_session(db, cookie_value)
    if user is None:
        raise AppError(401, "authentication_required", "Authentication is required.")
    return user
```

- [ ] **Step 6: Run session tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py -v
```

Expected: PASS/SKIP only for unavailable PostgreSQL.

- [ ] **Step 7: Commit**

```powershell
git add backend/app/core/config.py backend/app/services/session_service.py backend/app/api/deps.py backend/app/schemas/auth.py backend/tests/test_auth.py
git commit -m "feat: add dashboard session service"
```

---

### Task 3: Add GitHub App JWT And Installation Token Service

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/services/github_app_auth_service.py`
- Test: `backend/tests/test_github_app_auth.py`

- [ ] **Step 1: Write failing GitHub App auth tests**

Create `backend/tests/test_github_app_auth.py`:

```python
from datetime import UTC, datetime, timedelta

import pytest

from app.services import github_app_auth_service


def test_generate_app_jwt_requires_private_key(monkeypatch):
    monkeypatch.setenv("GITHUB_APP_ID", "123")
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_PATH", raising=False)
    github_app_auth_service.get_settings.cache_clear()

    with pytest.raises(Exception) as exc:
        github_app_auth_service.generate_app_jwt()

    assert "github_app_private_key" in str(exc.value)


def test_installation_token_is_not_persisted(monkeypatch):
    calls = []

    class FakeResponse:
        status_code = 201
        headers = {}

        def json(self):
            return {
                "token": "installation-token",
                "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            }

        @property
        def is_error(self):
            return False

    def fake_post(url, headers, timeout):
        calls.append((url, headers))
        return FakeResponse()

    monkeypatch.setattr(github_app_auth_service.httpx, "post", fake_post)
    monkeypatch.setattr(github_app_auth_service, "generate_app_jwt", lambda: "jwt-token")

    token = github_app_auth_service.generate_installation_token(42)

    assert token == "installation-token"
    assert calls[0][0].endswith("/app/installations/42/access_tokens")
    assert calls[0][1]["Authorization"] == "Bearer jwt-token"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_github_app_auth.py -v
```

Expected: FAIL because `github_app_auth_service` does not exist.

- [ ] **Step 3: Add dependencies**

Modify `backend/requirements.txt`:

```text
PyJWT>=2.10
cryptography>=43
```

- [ ] **Step 4: Implement GitHub App auth service**

Create `backend/app/services/github_app_auth_service.py`:

```python
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import jwt

from app.core.config import get_settings
from app.core.errors import AppError

INSTALLATION_TOKEN_CACHE: dict[int, tuple[str, datetime]] = {}


def _private_key() -> str:
    settings = get_settings()
    if settings.github_app_private_key:
        return settings.github_app_private_key.replace("\\n", "\n")
    if settings.github_app_private_key_path:
        return Path(settings.github_app_private_key_path).read_text(encoding="utf-8")
    raise AppError(
        503,
        "github_app_config_missing",
        "github_app_private_key or github_app_private_key_path is required.",
    )


def generate_app_jwt() -> str:
    settings = get_settings()
    if not settings.github_app_id:
        raise AppError(503, "github_app_config_missing", "GITHUB_APP_ID is required.")
    now = datetime.now(UTC)
    payload = {
        "iat": int((now - timedelta(seconds=60)).timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iss": settings.github_app_id,
    }
    try:
        return jwt.encode(payload, _private_key(), algorithm="RS256")
    except Exception as exc:
        raise AppError(503, "github_app_jwt_failed", "GitHub App JWT could not be generated.") from exc


def generate_installation_token(installation_id: int) -> str:
    cached = INSTALLATION_TOKEN_CACHE.get(installation_id)
    if cached and cached[1] > datetime.now(UTC) + timedelta(minutes=5):
        return cached[0]

    settings = get_settings()
    response = httpx.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {generate_app_jwt()}",
            "X-GitHub-Api-Version": settings.github_api_version,
        },
        timeout=20,
    )
    if response.is_error:
        raise AppError(
            503,
            "github_installation_token_failed",
            "GitHub installation token could not be generated.",
        )
    payload = response.json()
    token = payload["token"]
    expires_at = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
    INSTALLATION_TOKEN_CACHE[installation_id] = (token, expires_at)
    return token
```

- [ ] **Step 5: Run GitHub App auth tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_github_app_auth.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add backend/requirements.txt backend/app/services/github_app_auth_service.py backend/tests/test_github_app_auth.py
git commit -m "feat: add github app installation token service"
```

---

### Task 4: Add GitHub OAuth Login Routes

**Files:**
- Create: `backend/app/services/github_oauth_service.py`
- Create: `backend/app/api/routes_auth.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing auth route tests**

Append to `backend/tests/test_auth.py`:

```python
def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "authentication_required"


def test_login_redirects_to_github(monkeypatch, client):
    monkeypatch.setenv("GITHUB_APP_CLIENT_ID", "client-id")
    monkeypatch.setenv("AUTH_CALLBACK_URL", "http://localhost:8000/api/auth/github/callback")

    response = client.get("/api/auth/github/login", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert "github.com/login/oauth/authorize" in response.headers["location"]
    assert "client_id=client-id" in response.headers["location"]
```

- [ ] **Step 2: Run route tests and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py::test_me_requires_authentication tests\test_auth.py::test_login_redirects_to_github -v
```

Expected: FAIL with 404 for `/api/auth/me` or `/api/auth/github/login`.

- [ ] **Step 3: Implement OAuth service**

Create `backend/app/services/github_oauth_service.py`:

```python
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode
import secrets

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.github_connection import GitHubConnection
from app.models.user import User

AUTH_STATES: dict[str, str] = {}


@dataclass
class OAuthState:
    state: str
    verifier: str


def build_login_url() -> str:
    settings = get_settings()
    if not settings.github_app_client_id:
        raise AppError(503, "github_app_config_missing", "GITHUB_APP_CLIENT_ID is required.")
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    AUTH_STATES[state] = verifier
    query = urlencode(
        {
            "client_id": settings.github_app_client_id,
            "redirect_uri": settings.auth_callback_url,
            "state": state,
        }
    )
    return f"https://github.com/login/oauth/authorize?{query}"


def exchange_code_for_user(code: str, state: str, db: Session) -> User:
    if state not in AUTH_STATES:
        raise AppError(400, "github_oauth_state_invalid", "GitHub OAuth state is invalid.")
    AUTH_STATES.pop(state, None)
    settings = get_settings()
    response = httpx.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.github_app_client_id,
            "client_secret": settings.github_app_client_secret,
            "code": code,
            "redirect_uri": settings.auth_callback_url,
        },
        timeout=20,
    )
    if response.is_error:
        raise AppError(502, "github_oauth_exchange_failed", "GitHub OAuth exchange failed.")
    token = response.json().get("access_token")
    if not token:
        raise AppError(502, "github_oauth_exchange_failed", "GitHub OAuth exchange failed.")
    user_response = httpx.get(
        "https://api.github.com/user",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": settings.github_api_version,
        },
        timeout=20,
    )
    if user_response.is_error:
        raise AppError(502, "github_oauth_exchange_failed", "GitHub user identity could not be read.")
    return upsert_user_from_github(db, user_response.json(), token)


def upsert_user_from_github(db: Session, payload: dict, access_token: str) -> User:
    user = db.scalar(select(User).where(User.github_user_id == int(payload["id"])))
    if user is None:
        user = User(github_user_id=int(payload["id"]), github_login=payload["login"])
        db.add(user)
    user.github_login = payload["login"]
    user.name = payload.get("name")
    user.email = payload.get("email")
    user.avatar_url = payload.get("avatar_url")
    user.last_login_at = datetime.now(UTC)
    db.flush()
    connection = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if connection is None:
        connection = GitHubConnection(user_id=user.id, github_user_id=user.github_user_id, github_login=user.github_login)
        db.add(connection)
    connection.github_user_id = user.github_user_id
    connection.github_login = user.github_login
    connection.access_token_encrypted = token_crypto_service.encrypt_token(access_token)
    db.commit()
    db.refresh(user)
    return user
```

Import `token_crypto_service` in this file and create `backend/app/services/token_crypto_service.py` before this route is committed. Reuse the implementation from Task 5 Step 3.

- [ ] **Step 4: Implement auth routes**

Create `backend/app/api/routes_auth.py`:

```python
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import CurrentUserRead
from app.services import github_oauth_service, session_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=CurrentUserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return CurrentUserRead(
        id=current_user.id,
        github_user_id=current_user.github_user_id,
        github_login=current_user.github_login,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        has_github_connection=bool(current_user.github_connections),
    )


@router.get("/github/login")
def github_login():
    return RedirectResponse(github_oauth_service.build_login_url())


@router.get("/github/callback")
def github_callback(
    code: str = Query(),
    state: str = Query(),
    db: Session = Depends(get_db),
):
    user = github_oauth_service.exchange_code_for_user(code, state, db)
    created = session_service.create_session(db, user)
    settings = get_settings()
    response = RedirectResponse(settings.frontend_origin)
    response.set_cookie(
        settings.session_cookie_name,
        created.cookie_value,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        "qg_csrf",
        created.csrf_token,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/logout")
def logout(response: Response, qg_session: str | None = None, db: Session = Depends(get_db)):
    settings = get_settings()
    session_service.revoke_session(db, qg_session)
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie("qg_csrf", path="/")
    return {"status": "ok"}
```

Modify `backend/app/main.py`:

```python
from app.api import routes_auth

app.include_router(routes_auth.router)
```

- [ ] **Step 5: Run auth route tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py -v
```

Expected: PASS/SKIP only for unavailable PostgreSQL.

- [ ] **Step 6: Hold OAuth route changes until token encryption is present**

Do not stage or commit Task 4 independently. Continue immediately to Task 5, then commit the OAuth route and encryption changes together from Task 5 Step 6.

---

### Task 5: Add Token Encryption Before OAuth Route Commit

**Files:**
- Create: `backend/app/services/token_crypto_service.py`
- Modify: `backend/app/services/github_oauth_service.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing token encryption test**

Append to `backend/tests/test_auth.py`:

```python
from app.services import token_crypto_service


def test_token_crypto_round_trip(monkeypatch):
    key = token_crypto_service.generate_key()
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", key)
    token_crypto_service.get_settings.cache_clear()

    encrypted = token_crypto_service.encrypt_token("secret-token")

    assert encrypted != "secret-token"
    assert token_crypto_service.decrypt_token(encrypted) == "secret-token"
```

- [ ] **Step 2: Run token test and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py::test_token_crypto_round_trip -v
```

Expected: FAIL because `token_crypto_service` does not exist.

- [ ] **Step 3: Implement token crypto service**

Create `backend/app/services/token_crypto_service.py`:

```python
from cryptography.fernet import Fernet

from app.core.config import get_settings
from app.core.errors import AppError


def generate_key() -> str:
    return Fernet.generate_key().decode("ascii")


def _fernet() -> Fernet:
    key = get_settings().token_encryption_key
    if not key:
        raise AppError(503, "token_encryption_key_missing", "TOKEN_ENCRYPTION_KEY is required.")
    return Fernet(key.encode("ascii"))


def encrypt_token(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_token(value: str) -> str:
    return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
```

- [ ] **Step 4: Encrypt GitHub user access tokens**

Modify `backend/app/services/github_oauth_service.py`:

```python
from app.services import token_crypto_service

connection.access_token_encrypted = token_crypto_service.encrypt_token(access_token)
```

Tests that do not set `TOKEN_ENCRYPTION_KEY` should monkeypatch `token_crypto_service.encrypt_token` or set a generated key.

- [ ] **Step 5: Run auth tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py -v
```

Expected: PASS/SKIP only for unavailable PostgreSQL.

- [ ] **Step 6: Commit**

```powershell
git add backend/app/services/token_crypto_service.py backend/app/services/github_oauth_service.py backend/app/api/routes_auth.py backend/app/main.py backend/tests/test_auth.py
git commit -m "feat: add encrypted github app oauth login"
```

---

### Task 6: Add Installation Sync And Repository Access Authorization

**Files:**
- Create: `backend/app/services/github_installation_service.py`
- Create: `backend/app/api/routes_github_installations.py`
- Create: `backend/app/schemas/github_installation.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_github_installations.py`
- Test: `backend/tests/test_repository_authorization.py`

- [ ] **Step 1: Write failing installation sync test**

Create `backend/tests/test_github_installations.py`:

```python
from app.core.config import get_settings
from app.models.github_app_installation import GitHubAppInstallation
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.services import github_installation_service


def test_sync_installation_creates_repository_and_user_access(reset_database, db_session):
    user = User(github_user_id=1, github_login="octocat")
    db_session.add(user)
    db_session.commit()

    installation = github_installation_service.sync_installation_payload(
        db_session,
        user=user,
        installation_payload={
            "id": 99,
            "account": {"id": 100, "login": "octo-org", "type": "Organization"},
            "repository_selection": "selected",
            "permissions": {"contents": "read", "pull_requests": "read"},
            "events": ["pull_request"],
        },
        repositories_payload=[
            {
                "id": 456,
                "name": "quality-api",
                "full_name": "octo-org/quality-api",
                "owner": {"login": "octo-org"},
                "default_branch": "main",
                "permissions": {"admin": True, "push": True, "pull": True},
            }
        ],
    )

    assert installation.installation_id == 99
    assert db_session.query(Repository).filter_by(full_name="octo-org/quality-api").count() == 1
    assert db_session.query(UserRepositoryAccess).one().is_admin is True


def test_install_url_uses_configured_github_app_slug(monkeypatch, client):
    monkeypatch.setenv("GITHUB_APP_SLUG", "quality-gate-app")
    get_settings.cache_clear()

    response = client.get("/api/github/installations/install-url")

    assert response.status_code == 200
    assert response.json()["url"] == "https://github.com/apps/quality-gate-app/installations/new"
    get_settings.cache_clear()
```

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_github_installations.py -v
```

Expected: FAIL because `github_installation_service` does not exist.

- [ ] **Step 3: Implement installation service**

Create `backend/app/services/github_installation_service.py`:

```python
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.github_app_installation import GitHubAppInstallation
from app.models.installation_repository import InstallationRepository
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.models.coverage_execution_config import CoverageExecutionConfig
from app.models.quality_gate_config import QualityGateConfig


def sync_installation_payload(
    db: Session,
    *,
    user: User | None,
    installation_payload: dict,
    repositories_payload: list[dict],
) -> GitHubAppInstallation:
    installation = db.scalar(
        select(GitHubAppInstallation).where(
            GitHubAppInstallation.installation_id == int(installation_payload["id"])
        )
    )
    if installation is None:
        installation = GitHubAppInstallation(installation_id=int(installation_payload["id"]))
        db.add(installation)
    account = installation_payload["account"]
    installation.account_id = int(account["id"])
    installation.account_login = account["login"]
    installation.account_type = account["type"]
    installation.repository_selection = installation_payload.get("repository_selection")
    installation.permissions_json = installation_payload.get("permissions") or {}
    installation.events_json = installation_payload.get("events") or []
    installation.active = True
    installation.suspended_at = None
    db.flush()

    for repo_payload in repositories_payload:
        repository = _upsert_repository(db, repo_payload)
        link = db.scalar(
            select(InstallationRepository).where(
                InstallationRepository.installation_id == installation.id,
                InstallationRepository.repository_id == repository.id,
            )
        )
        if link is None:
            link = InstallationRepository(
                installation_id=installation.id,
                repository_id=repository.id,
                github_repo_id=repository.github_repo_id,
                full_name=repository.full_name,
            )
            db.add(link)
        if user is not None:
            _upsert_user_access(db, user, repository, installation, repo_payload.get("permissions") or {})
    db.commit()
    db.refresh(installation)
    return installation


def _upsert_repository(db: Session, payload: dict) -> Repository:
    repository = db.scalar(select(Repository).where(Repository.github_repo_id == int(payload["id"])))
    if repository is None:
        repository = Repository(github_repo_id=int(payload["id"]))
        repository.quality_gate_config = QualityGateConfig()
        repository.coverage_execution_config = CoverageExecutionConfig()
        db.add(repository)
    repository.owner = payload["owner"]["login"]
    repository.name = payload["name"]
    repository.full_name = payload["full_name"]
    repository.default_branch = payload.get("default_branch") or "main"
    db.flush()
    return repository


def _upsert_user_access(
    db: Session,
    user: User,
    repository: Repository,
    installation: GitHubAppInstallation,
    permissions: dict,
) -> UserRepositoryAccess:
    access = db.scalar(
        select(UserRepositoryAccess).where(
            UserRepositoryAccess.user_id == user.id,
            UserRepositoryAccess.repository_id == repository.id,
        )
    )
    if access is None:
        access = UserRepositoryAccess(user_id=user.id, repository_id=repository.id, installation_id=installation.id)
        db.add(access)
    access.installation_id = installation.id
    access.permission = _permission_name(permissions)
    access.is_admin = bool(permissions.get("admin"))
    access.synced_at = datetime.now(UTC)
    return access


def _permission_name(permissions: dict) -> str | None:
    for name in ("admin", "maintain", "push", "triage", "pull"):
        if permissions.get(name):
            return name
    return None


def require_repository_access(db: Session, user: User, repository_id: UUID) -> UserRepositoryAccess:
    access = db.scalar(
        select(UserRepositoryAccess).where(
            UserRepositoryAccess.user_id == user.id,
            UserRepositoryAccess.repository_id == repository_id,
        )
    )
    if access is None:
        raise AppError(403, "repository_access_denied", "You do not have access to this repository.")
    return access


def require_repository_admin(db: Session, user: User, repository_id: UUID) -> UserRepositoryAccess:
    access = require_repository_access(db, user, repository_id)
    if not access.is_admin:
        raise AppError(403, "repository_admin_required", "Repository admin permission is required.")
    return access
```

- [ ] **Step 4: Add installation schemas and routes**

Create `backend/app/schemas/github_installation.py`:

```python
from pydantic import BaseModel


class GitHubInstallationRead(BaseModel):
    installation_id: int
    account_login: str
    account_type: str
    active: bool


class GitHubInstallUrlRead(BaseModel):
    url: str
```

Create `backend/app/api/routes_github_installations.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.models.user import User
from app.schemas.github_installation import GitHubInstallationRead, GitHubInstallUrlRead

router = APIRouter(prefix="/api/github/installations", tags=["github-installations"])


@router.get("/install-url", response_model=GitHubInstallUrlRead)
def get_install_url():
    slug = get_settings().github_app_slug
    if not slug:
        raise AppError(503, "github_app_slug_missing", "GITHUB_APP_SLUG is required.")
    return GitHubInstallUrlRead(url=f"https://github.com/apps/{slug}/installations/new")


@router.get("", response_model=list[GitHubInstallationRead])
def list_installations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return [
        GitHubInstallationRead(
            installation_id=access.installation.installation_id,
            account_login=access.installation.account_login,
            account_type=access.installation.account_type,
            active=access.installation.active,
        )
        for access in current_user.repository_access
    ]
```

Modify `backend/app/main.py`:

```python
from app.api import routes_github_installations

app.include_router(routes_github_installations.router)
```

The external GitHub API-backed sync endpoint is added after the low-level client is refactored in Task 7.

- [ ] **Step 5: Run installation tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_github_installations.py -v
```

Expected: PASS/SKIP only for unavailable PostgreSQL.

- [ ] **Step 6: Commit**

```powershell
git add backend/app/services/github_installation_service.py backend/app/api/routes_github_installations.py backend/app/schemas/github_installation.py backend/app/main.py backend/tests/test_github_installations.py
git commit -m "feat: sync github app installations"
```

---

### Task 7: Protect Repository And Config APIs With User Access

**Files:**
- Modify: `backend/app/api/routes_repositories.py`
- Modify: `backend/app/api/routes_quality_gate.py`
- Modify: `backend/app/api/routes_coverage_execution_config.py`
- Modify: `backend/app/services/repository_service.py`
- Test: `backend/tests/test_repository_authorization.py`

- [ ] **Step 1: Write failing authorization tests**

Create `backend/tests/test_repository_authorization.py`:

```python
from datetime import UTC, datetime

from app.models.github_app_installation import GitHubAppInstallation
from app.models.repository import Repository
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess
from app.services import session_service


def create_user_repo_access(db_session, *, is_admin: bool):
    user = User(github_user_id=10 if is_admin else 11, github_login="admin" if is_admin else "viewer")
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


def test_repository_list_is_filtered_to_current_user(client, reset_database, db_session):
    _user, repository, cookie = create_user_repo_access(db_session, is_admin=False)

    response = client.get("/api/repositories", cookies={"qg_session": cookie})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [str(repository.id)]


def test_non_admin_cannot_update_quality_gate_config(client, reset_database, db_session):
    _user, repository, cookie = create_user_repo_access(db_session, is_admin=False)

    response = client.put(
        f"/api/repositories/{repository.id}/quality-gate-config",
        cookies={"qg_session": cookie},
        json={"min_total_coverage": 90},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "repository_admin_required"
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_repository_authorization.py -v
```

Expected: FAIL because repository routes are currently unauthenticated.

- [ ] **Step 3: Update repository service and route**

Modify `backend/app/services/repository_service.py`:

```python
from app.models.user import User
from app.models.user_repository_access import UserRepositoryAccess

def list_repositories_for_user(db: Session, user: User) -> list[Repository]:
    return list(
        db.scalars(
            select(Repository)
            .join(UserRepositoryAccess, UserRepositoryAccess.repository_id == Repository.id)
            .where(UserRepositoryAccess.user_id == user.id)
            .order_by(Repository.full_name)
        )
    )
```

Modify `backend/app/api/routes_repositories.py`:

```python
from app.api.deps import get_current_user
from app.models.user import User
from app.services.github_installation_service import require_repository_access

@router.get("", response_model=list[RepositoryRead])
def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return repository_service.list_repositories_for_user(db, current_user)

@router.get("/{repository_id}", response_model=RepositoryRead)
def get_repository(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    return repository_service.get_repository(db, repository_id)
```

Remove the public `POST /api/repositories` and `POST /api/repositories/github` route functions in Task 12 after frontend/API clients are updated.

- [ ] **Step 4: Require admin for config writes**

Modify `backend/app/api/routes_quality_gate.py`:

```python
from app.api.deps import get_current_user
from app.models.user import User
from app.services.github_installation_service import require_repository_access, require_repository_admin

def get_quality_gate_config(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    return quality_gate_service.get_quality_gate_config(db, repository_id)

def update_quality_gate_config(
    repository_id: UUID,
    payload: QualityGateConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_admin(db, current_user, repository_id)
    return quality_gate_service.update_quality_gate_config(db, repository_id, payload)
```

Modify `backend/app/api/routes_coverage_execution_config.py` the same way:

```python
from app.api.deps import get_current_user
from app.models.user import User
from app.services.github_installation_service import require_repository_access, require_repository_admin

def get_coverage_execution_config(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    return coverage_execution_config_service.get_coverage_execution_config(db, repository_id)

def update_coverage_execution_config(
    repository_id: UUID,
    payload: CoverageExecutionConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_admin(db, current_user, repository_id)
    return coverage_execution_config_service.update_coverage_execution_config(db, repository_id, payload)
```

- [ ] **Step 5: Run authorization tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_repository_authorization.py -v
```

Expected: PASS/SKIP only for unavailable PostgreSQL.

- [ ] **Step 6: Commit**

```powershell
git add backend/app/api/routes_repositories.py backend/app/api/routes_quality_gate.py backend/app/api/routes_coverage_execution_config.py backend/app/services/repository_service.py backend/tests/test_repository_authorization.py
git commit -m "feat: authorize repository and config access"
```

---

### Task 8: Refactor GitHub Client To Use Installation Tokens

**Files:**
- Modify: `backend/app/services/github_service.py`
- Modify: `backend/app/services/github_publication_service.py`
- Modify: `backend/app/services/runner_service.py`
- Test: `backend/tests/test_github_client_context.py`
- Test: `backend/tests/test_github_publication.py`

- [ ] **Step 1: Write failing token injection test**

Add to `backend/tests/test_github_client_context.py`:

```python
def test_github_client_uses_provided_installation_token(monkeypatch):
    seen_headers = []

    class FakeResponse:
        status_code = 200
        headers = {}

        def json(self):
            return []

        @property
        def is_error(self):
            return False

    def fake_get(url, headers, params=None, timeout=20):
        seen_headers.append(headers)
        return FakeResponse()

    monkeypatch.setattr("app.services.github_service.httpx.get", fake_get)

    client = GitHubClient("installation-token")
    client.list_pull_requests("octo-org", "quality-api")

    assert seen_headers[0]["Authorization"] == "Bearer installation-token"
```

- [ ] **Step 2: Run test and verify current behavior**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_github_client_context.py::test_github_client_uses_provided_installation_token -v
```

Expected: PASS if current `GitHubClient` already accepts token injection; if PASS, keep it and move to Step 3. If FAIL, update `GitHubClient.__init__` to require token and headers to use that token.

- [ ] **Step 3: Add installation-token client helpers**

Modify `backend/app/services/github_service.py`:

```python
from app.services import github_app_auth_service, github_installation_service

def installation_client_for_repository(db: Session, repository_id) -> GitHubClient:
    access_or_installation = github_installation_service.get_active_installation_for_repository(db, repository_id)
    token = github_app_auth_service.generate_installation_token(access_or_installation.installation.installation_id)
    return GitHubClient(token)
```

Add to `backend/app/services/github_installation_service.py`:

```python
from app.models.installation_repository import InstallationRepository


def get_active_installation_for_repository(db: Session, repository_id: UUID) -> InstallationRepository:
    link = db.scalar(
        select(InstallationRepository)
        .join(GitHubAppInstallation, GitHubAppInstallation.id == InstallationRepository.installation_id)
        .where(
            InstallationRepository.repository_id == repository_id,
            GitHubAppInstallation.active.is_(True),
            GitHubAppInstallation.suspended_at.is_(None),
        )
        .limit(1)
    )
    if link is None:
        raise AppError(409, "github_installation_required", "An active GitHub App installation is required.")
    return link
```

- [ ] **Step 4: Redact clone tokens**

Modify `backend/app/services/runner_service.py`:

```python
def repository_clone_url(owner: str, name: str, token: str | None = None) -> str:
    if token:
        return f"https://x-access-token:{token}@github.com/{owner}/{name}.git"
    return f"https://github.com/{owner}/{name}.git"


def redacted_command(command: str) -> str:
    return re.sub(r"x-access-token:[^@]+@", "x-access-token:***@", command)
```

Update `CommandResult.to_snapshot()` to use redacted command:

```python
"command": redacted_command(self.command),
```

Import `re`.

- [ ] **Step 5: Use installation token for publication**

Modify `backend/app/services/github_publication_service.py`:

```python
from app.services import github_app_auth_service, github_installation_service

installation_link = github_installation_service.get_active_installation_for_repository(db, run.repository_id)
client = GitHubClient(
    github_app_auth_service.generate_installation_token(
        installation_link.installation.installation_id
    )
)
```

Remove `get_settings().github_token` usage for publication.

- [ ] **Step 6: Run GitHub client/publication tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_github_client_context.py tests\test_github_publication.py -v
```

Expected: PASS/SKIP only for unavailable PostgreSQL.

- [ ] **Step 7: Commit**

```powershell
git add backend/app/services/github_service.py backend/app/services/github_installation_service.py backend/app/services/github_publication_service.py backend/app/services/runner_service.py backend/tests/test_github_client_context.py backend/tests/test_github_publication.py
git commit -m "feat: use installation tokens for github operations"
```

---

### Task 9: Add Manual Live Pull Request Analysis Endpoint

**Files:**
- Modify: `backend/app/api/routes_repositories.py`
- Modify: `backend/app/services/analysis_service.py`
- Modify: `backend/app/services/github_service.py`
- Test: `backend/tests/test_manual_pr_analysis.py`

- [ ] **Step 1: Write failing manual analysis tests**

Create `backend/tests/test_manual_pr_analysis.py`:

```python
from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource


def test_manual_analyze_requires_repository_access(client, reset_database, repository):
    response = client.post(f"/api/repositories/{repository['id']}/pull-requests/1/analyze")

    assert response.status_code == 401


def test_manual_analyze_creates_and_executes_real_run(monkeypatch, client, reset_database, db_session):
    user, repository, cookie = create_user_repo_access(db_session, is_admin=False)

    monkeypatch.setattr(
        "app.services.github_service.get_repository_pull_request_context",
        lambda db, repository_id, pr_number: {
            "pull_request": {
                "number": pr_number,
                "title": "Improve quality",
                "body": None,
                "state": "open",
                "draft": False,
                "author_login": "octocat",
                "html_url": "https://github.com/octo-org/quality-api/pull/1",
                "base_ref": "main",
                "head_ref": "feature",
                "head_sha": "head-sha",
                "base_sha": "base-sha",
                "created_at": "2026-06-23T00:00:00Z",
                "updated_at": "2026-06-23T00:00:00Z",
            },
            "changed_files": [],
            "diff_snapshot": "diff --git a/a.py b/a.py",
            "diff_truncated": False,
        },
    )
    monkeypatch.setattr(
        "app.services.analysis_execution_service.execute_analysis_run",
        lambda db, analysis_run_id: db.get(__import__("app.models.analysis_run", fromlist=["AnalysisRun"]).AnalysisRun, analysis_run_id),
    )

    response = client.post(
        f"/api/repositories/{repository.id}/pull-requests/1/analyze",
        cookies={"qg_session": cookie},
    )

    assert response.status_code == 200
    assert response.json()["trigger_source"] == AnalysisTriggerSource.MANUAL.value
```

Use or move the `create_user_repo_access` helper from `test_repository_authorization.py` into `backend/tests/conftest.py` if test import sharing becomes awkward.

- [ ] **Step 2: Run manual analysis test and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_manual_pr_analysis.py -v
```

Expected: FAIL because analyze endpoint does not exist.

- [ ] **Step 3: Add analysis service helper**

Modify `backend/app/services/analysis_service.py`:

```python
from app.schemas.github import PullRequestContextRead

def create_or_reuse_manual_analysis_run(
    db: Session,
    repository_id: UUID,
    context: PullRequestContextRead | dict,
) -> AnalysisRun:
    context_model = _coerce_context(context)
    existing = get_analysis_run_by_pr_head(
        db,
        repository_id,
        context_model.pull_request.number,
        context_model.pull_request.head_sha,
    )
    if existing is not None:
        return get_analysis_run(db, existing.id)
    run = AnalysisRun(
        repository_id=repository_id,
        pr_number=context_model.pull_request.number,
        head_sha=context_model.pull_request.head_sha,
        status=AnalysisRunStatus.PENDING,
        decision=None,
        trigger_source=AnalysisTriggerSource.MANUAL,
        score=None,
        coverage_result_json={},
        security_result_json={},
        technical_debt_result_json={},
        ai_review_json={},
        pull_request_snapshot_json=context_model.pull_request.model_dump(mode="json"),
        changed_files_snapshot_json=[
            changed_file.model_dump(mode="json")
            for changed_file in context_model.changed_files
        ],
        diff_snapshot=context_model.diff_snapshot,
        diff_truncated=context_model.diff_truncated,
        final_report_markdown=None,
        error_message=None,
        started_at=None,
        finished_at=None,
    )
    return _commit_new_run_or_reuse(db, run)
```

- [ ] **Step 4: Add route**

Modify `backend/app/api/routes_repositories.py`:

```python
from app.services import analysis_execution_service, analysis_service
from app.services.github_installation_service import require_repository_access

@router.post(
    "/{repository_id}/pull-requests/{pr_number}/analyze",
    response_model=AnalysisRunDetail,
)
def analyze_pull_request(
    repository_id: UUID,
    pr_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_repository_access(db, current_user, repository_id)
    context = github_service.get_repository_pull_request_context(db, repository_id, pr_number)
    run = analysis_service.create_or_reuse_manual_analysis_run(db, repository_id, context)
    if run.status == AnalysisRunStatus.PENDING:
        return analysis_execution_service.execute_analysis_run(db, run.id)
    return analysis_service.get_analysis_run(db, run.id)
```

Add imports for `AnalysisRunDetail`, `AnalysisRunStatus`, `User`, and auth dependency.

- [ ] **Step 5: Run manual analysis tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_manual_pr_analysis.py -v
```

Expected: PASS/SKIP only for unavailable PostgreSQL.

- [ ] **Step 6: Commit**

```powershell
git add backend/app/api/routes_repositories.py backend/app/services/analysis_service.py backend/tests/test_manual_pr_analysis.py backend/tests/conftest.py
git commit -m "feat: add manual live pull request analysis"
```

---

### Task 10: Execute Pull Request Webhooks Automatically

**Files:**
- Modify: `backend/app/api/routes_github_webhooks.py`
- Modify: `backend/app/services/github_webhook_service.py`
- Test: `backend/tests/test_github_webhooks.py`

- [ ] **Step 1: Write failing webhook scheduling test**

Add to `backend/tests/test_github_webhooks.py`:

```python
def test_pull_request_webhook_schedules_analysis_execution(monkeypatch, client, reset_database, repository):
    executed = []

    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "secret")
    monkeypatch.setattr(
        "app.services.github_webhook_service._has_valid_signature",
        lambda body, secret, signature_header: True,
    )
    monkeypatch.setattr(
        "app.services.github_webhook_service.GitHubClient.get_pull_request_context",
        lambda self, owner, name, pr_number: {
            "pull_request": {
                "number": pr_number,
                "title": "Improve quality",
                "body": None,
                "state": "open",
                "draft": False,
                "author_login": "octocat",
                "html_url": "https://github.com/octo-org/quality-api/pull/1",
                "base_ref": "main",
                "head_ref": "feature",
                "head_sha": "head-sha",
                "base_sha": "base-sha",
                "created_at": "2026-06-23T00:00:00Z",
                "updated_at": "2026-06-23T00:00:00Z",
            },
            "changed_files": [],
            "diff_snapshot": "diff --git a/a.py b/a.py",
            "diff_truncated": False,
        },
    )
    monkeypatch.setattr(
        "app.services.analysis_execution_service.execute_analysis_run",
        lambda db, analysis_run_id: executed.append(str(analysis_run_id)),
    )

    response = client.post(
        "/api/github/webhooks",
        headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": "sha256=test"},
        json={
            "action": "opened",
            "installation": {"id": 99},
            "repository": {"full_name": repository["full_name"]},
            "pull_request": {
                "number": 1,
                "title": "Improve quality",
                "body": None,
                "state": "open",
                "draft": False,
                "html_url": "https://github.com/octo-org/quality-api/pull/1",
                "user": {"login": "octocat"},
                "base": {"ref": "main", "sha": "base-sha"},
                "head": {"ref": "feature", "sha": "head-sha"},
                "created_at": "2026-06-23T00:00:00Z",
                "updated_at": "2026-06-23T00:00:00Z",
            },
        },
    )

    assert response.status_code == 202
    assert response.json()["analysis_run_id"] is not None
    assert executed
```

- [ ] **Step 2: Run webhook test and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_github_webhooks.py::test_pull_request_webhook_schedules_analysis_execution -v
```

Expected: FAIL because webhook currently creates pending runs without execution.

- [ ] **Step 3: Add BackgroundTasks to route**

Modify `backend/app/api/routes_github_webhooks.py`:

```python
from fastapi import BackgroundTasks

async def receive_github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str | None = Header(default=None, alias="X-GitHub-Event"),
    x_hub_signature_256: str | None = Header(
        default=None,
        alias="X-Hub-Signature-256",
    ),
    db: Session = Depends(get_db),
):
    body = await request.body()
    return github_webhook_service.process_github_webhook(
        db,
        body,
        x_github_event,
        x_hub_signature_256,
        background_tasks=background_tasks,
    )
```

- [ ] **Step 4: Schedule execution in webhook service**

Modify `backend/app/services/github_webhook_service.py`:

```python
from fastapi import BackgroundTasks
from app.services import analysis_execution_service

def process_github_webhook(
    db: Session,
    body: bytes,
    event: str | None,
    signature: str | None,
    background_tasks: BackgroundTasks | None = None,
) -> GitHubWebhookResult:
    run = create_or_reuse_webhook_analysis_run(db, body, event, signature)
    created_new = run.status == AnalysisRunStatus.PENDING
    if created_new:
        if background_tasks is not None:
            background_tasks.add_task(_execute_run_by_id, run.id)
        else:
            analysis_execution_service.execute_analysis_run(db, run.id)
```

Add helper:

```python
def _execute_run_by_id(analysis_run_id):
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        analysis_execution_service.execute_analysis_run(db, analysis_run_id)
    finally:
        db.close()
```

Import `AnalysisRunStatus`.

- [ ] **Step 5: Run webhook tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_github_webhooks.py -v
```

Expected: PASS/SKIP only for unavailable PostgreSQL.

- [ ] **Step 6: Commit**

```powershell
git add backend/app/api/routes_github_webhooks.py backend/app/services/github_webhook_service.py backend/tests/test_github_webhooks.py
git commit -m "feat: execute pull request webhooks automatically"
```

---

### Task 11: Remove Mock Analysis Backend

**Files:**
- Modify: `backend/app/models/enums.py`
- Modify: `backend/app/schemas/analysis.py`
- Modify: `backend/app/services/analysis_service.py`
- Modify: `backend/app/api/routes_analysis.py`
- Create: `backend/alembic/versions/20260623_0006_remove_mock_analysis.py`
- Modify tests that reference mock creation.

- [ ] **Step 1: Write failing removal tests**

Add to `backend/tests/test_analysis_runs.py`:

```python
def test_mock_analysis_endpoint_is_removed(client, repository):
    response = client.post(
        f"/api/repositories/{repository['id']}/analysis-runs/mock",
        json={"scenario": "passing", "pr_number": 1, "head_sha": "abc"},
    )

    assert response.status_code == 404
```

- [ ] **Step 2: Run removal test and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_analysis_runs.py::test_mock_analysis_endpoint_is_removed -v
```

Expected: FAIL because endpoint currently exists.

- [ ] **Step 3: Remove mock schemas and route**

Modify `backend/app/schemas/analysis.py`:

```python
Remove MockScenario and MockAnalysisRunCreate.
```

Modify `backend/app/api/routes_analysis.py`:

```python
Remove the create_mock_analysis_run route and MockAnalysisRunCreate import.
```

- [ ] **Step 4: Remove mock service code**

Modify `backend/app/services/analysis_service.py`:

```python
Remove SCENARIOS, create_mock_analysis_run, and _render_report.
```

Keep shared helpers:

```python
list_analysis_runs
get_analysis_run
get_analysis_run_by_pr_head
create_or_reuse_webhook_analysis_run
create_or_reuse_error_webhook_analysis_run
create_or_reuse_manual_analysis_run
_coerce_context
_commit_new_run_or_reuse
```

- [ ] **Step 5: Remove enum product value**

Modify `backend/app/models/enums.py`:

```python
class AnalysisTriggerSource(str, Enum):
    MANUAL = "manual"
    GITHUB_WEBHOOK = "github_webhook"
```

Create `backend/alembic/versions/20260623_0006_remove_mock_analysis.py`:

```python
"""remove mock analysis

Revision ID: 20260623_0006
Revises: 20260623_0005
Create Date: 2026-06-23
"""

from typing import Sequence

from alembic import op

revision: str = "20260623_0006"
down_revision: str | None = "20260623_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM analysis_findings
        WHERE analysis_run_id IN (
            SELECT id FROM analysis_runs WHERE trigger_source = 'mock'
        )
        """
    )
    op.execute("DELETE FROM analysis_runs WHERE trigger_source = 'mock'")
    op.execute("ALTER TYPE analysis_trigger_source RENAME TO analysis_trigger_source_old")
    op.execute("CREATE TYPE analysis_trigger_source AS ENUM ('manual', 'github_webhook')")
    op.execute(
        """
        ALTER TABLE analysis_runs
        ALTER COLUMN trigger_source TYPE analysis_trigger_source
        USING trigger_source::text::analysis_trigger_source
        """
    )
    op.execute("DROP TYPE analysis_trigger_source_old")


def downgrade() -> None:
    op.execute("ALTER TYPE analysis_trigger_source RENAME TO analysis_trigger_source_old")
    op.execute("CREATE TYPE analysis_trigger_source AS ENUM ('mock', 'manual', 'github_webhook')")
    op.execute(
        """
        ALTER TABLE analysis_runs
        ALTER COLUMN trigger_source TYPE analysis_trigger_source
        USING trigger_source::text::analysis_trigger_source
        """
    )
    op.execute("DROP TYPE analysis_trigger_source_old")
```

- [ ] **Step 6: Update tests**

In `backend/tests/test_analysis_runs.py`, delete assertions for `MockScenario`, `MockAnalysisRunCreate`, and `POST /api/analysis-runs/mock`. Keep generic analysis-detail/list tests by building `AnalysisRun` rows directly with `AnalysisTriggerSource.MANUAL` or `AnalysisTriggerSource.GITHUB_WEBHOOK`. Confirm manual creation behavior is covered in `backend/tests/test_manual_pr_analysis.py` and webhook creation/execution behavior is covered in `backend/tests/test_github_webhooks.py`.

- [ ] **Step 7: Run analysis tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_analysis_runs.py tests\test_manual_pr_analysis.py tests\test_github_webhooks.py -v
```

Expected: PASS/SKIP only for unavailable PostgreSQL.

- [ ] **Step 8: Commit**

```powershell
git add backend/app/models/enums.py backend/app/schemas/analysis.py backend/app/services/analysis_service.py backend/app/api/routes_analysis.py backend/alembic/versions/20260623_0006_remove_mock_analysis.py backend/tests
git commit -m "feat: remove mock analysis backend"
```

---

### Task 12: Remove Manual Repository Creation Product Routes

**Files:**
- Modify: `backend/app/api/routes_repositories.py`
- Modify: `backend/app/services/repository_service.py`
- Modify: `backend/tests/test_repositories.py`

- [ ] **Step 1: Write failing route removal test**

Modify `backend/tests/test_repositories.py`:

```python
def test_manual_repository_creation_endpoint_is_removed(client):
    response = client.post(
        "/api/repositories",
        json={"owner": "octo-org", "name": "quality-api", "default_branch": "main"},
    )

    assert response.status_code == 404
```

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_repositories.py::test_manual_repository_creation_endpoint_is_removed -v
```

Expected: FAIL because `POST /api/repositories` currently exists.

- [ ] **Step 3: Remove public creation routes**

Modify `backend/app/api/routes_repositories.py`:

```python
Remove create_repository and create_repository_from_github route functions.
Remove RepositoryCreate and GitHubRepositoryCreate imports when unused.
```

Keep `repository_service.create_repository` only for internal installation sync and test fixture setup. Verify `routes_repositories.py` exposes no public route that accepts `RepositoryCreate` or `GitHubRepositoryCreate`.

- [ ] **Step 4: Run repository tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_repositories.py tests\test_repository_authorization.py -v
```

Expected: PASS/SKIP only for unavailable PostgreSQL.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/api/routes_repositories.py backend/tests/test_repositories.py
git commit -m "feat: remove manual repository creation routes"
```

---

### Task 13: Add Frontend Auth Gate And GitHub Installation Entry

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/components/AuthGate.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Add API types**

Modify `frontend/src/types/api.ts`:

```typescript
export type CurrentUser = {
  id: string;
  github_user_id: number;
  github_login: string;
  name: string | null;
  avatar_url: string | null;
  has_github_connection: boolean;
};

export type GitHubInstallation = {
  installation_id: number;
  account_login: string;
  account_type: string;
  active: boolean;
};
```

Remove `MockScenario`.

- [ ] **Step 2: Add API client methods and remove mock client**

Modify `frontend/src/api/client.ts`:

```typescript
import type { CurrentUser, GitHubInstallation } from "../types/api";

export function getCurrentUser() {
  return request<CurrentUser>("/api/auth/me");
}

export function logout() {
  return request<{ status: string }>("/api/auth/logout", { method: "POST" });
}

export function listGitHubInstallations() {
  return request<GitHubInstallation[]>("/api/github/installations");
}

export function analyzePullRequest(repositoryId: string, prNumber: number) {
  return request<AnalysisRunDetail>(
    `/api/repositories/${repositoryId}/pull-requests/${prNumber}/analyze`,
    { method: "POST" }
  );
}
```

Remove:

```typescript
createRepository
createGitHubRepository
createMockAnalysisRun
MockScenario import
```

- [ ] **Step 3: Create AuthGate**

Create `frontend/src/components/AuthGate.tsx`:

```typescript
import { ReactNode, useEffect, useState } from "react";

import { getCurrentUser } from "../api/client";
import ErrorMessage from "./ErrorMessage";
import LoadingBlock from "./LoadingBlock";
import type { CurrentUser } from "../types/api";

export default function AuthGate({
  children
}: {
  children: (user: CurrentUser) => ReactNode;
}) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    getCurrentUser()
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <LoadingBlock label="Loading account" />;
  }

  if (!user) {
    return (
      <div className="login-screen">
        <ErrorMessage error={error} />
        <a className="button primary" href="/api/auth/github/login">
          Sign in with GitHub
        </a>
      </div>
    );
  }

  return <>{children(user)}</>;
}
```

- [ ] **Step 4: Wrap app shell**

Modify `frontend/src/App.tsx`:

```typescript
import AuthGate from "./components/AuthGate";

export default function App() {
  return (
    <AuthGate>
      {(user) => (
        <div className="app-shell">
          <AppNavigation />
          <div className="user-chip">{user.github_login}</div>
          <AppRoutes />
        </div>
      )}
    </AuthGate>
  );
}
```

Keep existing routes inside the authenticated shell.

- [ ] **Step 5: Run frontend build**

Run:

```powershell
npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add frontend/src/types/api.ts frontend/src/api/client.ts frontend/src/components/AuthGate.tsx frontend/src/App.tsx
git commit -m "feat: add github authenticated app shell"
```

---

### Task 14: Remove Mock UI And Add Live PR Analyze Action

**Files:**
- Modify: `frontend/src/pages/RepositoriesPage.tsx`
- Modify: `frontend/src/pages/RepositoryPullRequestsPage.tsx`
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/pages/RepositoryQualityGateConfigPage.tsx`
- Modify: `frontend/src/pages/AnalysisDetailPage.tsx`
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Remove repository creation UI**

Modify `frontend/src/pages/RepositoriesPage.tsx` to:

```typescript
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listGitHubInstallations, listRepositories } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorMessage from "../components/ErrorMessage";
import type { GitHubInstallation, Repository } from "../types/api";

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [installations, setInstallations] = useState<GitHubInstallation[]>([]);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    listRepositories().then(setRepositories).catch(setError);
    listGitHubInstallations().then(setInstallations).catch(setError);
  }, []);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Repositories</p>
          <h1>GitHub Repositories</h1>
        </div>
        <a className="button primary" href="https://github.com/apps">
          Manage GitHub App
        </a>
      </header>
      <ErrorMessage error={error} />
      {installations.length === 0 && repositories.length === 0 ? (
        <EmptyState title="No GitHub App installations">
          Install the GitHub App to choose repositories for analysis.
        </EmptyState>
      ) : (
        <section className="panel">
          <div className="panel-header">
            <h2>Accessible Repositories</h2>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Repository</th>
                  <th>Default branch</th>
                  <th>GitHub ID</th>
                </tr>
              </thead>
              <tbody>
                {repositories.map((repository) => (
                  <tr key={repository.id}>
                    <td>
                      <Link to={`/repositories/${repository.id}`}>
                        {repository.full_name}
                      </Link>
                    </td>
                    <td>{repository.default_branch}</td>
                    <td>{repository.github_repo_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
```

Use `GET /api/github/installations/install-url`, created in Task 6 Step 4, for the GitHub App installation URL. Keep the login page focused on `/api/auth/github/login` and do not hard-code a GitHub App slug in the frontend.

- [ ] **Step 2: Remove mock controls from PR page**

Modify `frontend/src/pages/RepositoryPullRequestsPage.tsx`:

```typescript
Remove selectedScenario, manualPrNumber, manualHeadSha, scenarios, createScenario, handleManualSubmit, and the Mock Analysis Controls section.
```

Replace action handling:

```typescript
import { analyzePullRequest, listPullRequests } from "../api/client";

async function analyze(prNumber: number) {
  setActionError(null);
  try {
    const run = await analyzePullRequest(repository.id, prNumber);
    navigate(`/analysis-runs/${run.id}`);
  } catch (caught) {
    setActionError(caught);
  }
}
```

Update `PullRequestActions`:

```typescript
function PullRequestActions({
  onAnalyze,
  pullRequest
}: {
  onAnalyze: (prNumber: number) => void;
  pullRequest: GitHubPullRequest;
}) {
  const run = pullRequest.review_state.analysis_run;
  if (!run || pullRequest.review_state.state === "outdated") {
    return (
      <button
        className="button small primary"
        onClick={() => onAnalyze(pullRequest.number)}
        type="button"
      >
        Analyze
      </button>
    );
  }
  return <Link to={`/analysis-runs/${run.id}`}>View detail</Link>;
}
```

- [ ] **Step 3: Remove mock text from dashboard**

Modify `frontend/src/pages/DashboardPage.tsx`:

```typescript
Replace "Register a repository to start creating mock Analysis Runs." with "Install the GitHub App to start analyzing Pull Requests."
Replace "Create a mock Analysis Run from a repository workspace." with "Analyze a Pull Request from a repository workspace."
Replace "Findings will appear after failing mock scenarios." with "Findings will appear after Pull Request analyses."
```

- [ ] **Step 4: Run frontend build**

Run:

```powershell
npm run build
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add frontend/src/pages/RepositoriesPage.tsx frontend/src/pages/RepositoryPullRequestsPage.tsx frontend/src/pages/DashboardPage.tsx frontend/src/api/client.ts frontend/src/types/api.ts
git commit -m "feat: remove mock ui and analyze live prs"
```

---

### Task 15: Update README And Environment Docs

**Files:**
- Modify: `.env.example`
- Modify: `README.md`

- [ ] **Step 1: Update `.env.example`**

Add:

```env
GITHUB_APP_ID=
GITHUB_APP_CLIENT_ID=
GITHUB_APP_CLIENT_SECRET=
GITHUB_APP_PRIVATE_KEY=
GITHUB_APP_PRIVATE_KEY_PATH=
GITHUB_APP_SLUG=
GITHUB_WEBHOOK_SECRET=
GITHUB_API_VERSION=2022-11-28
SESSION_SECRET=change-me
SESSION_COOKIE_NAME=qg_session
SESSION_COOKIE_SECURE=false
TOKEN_ENCRYPTION_KEY=
AUTH_CALLBACK_URL=http://localhost:8000/api/auth/github/callback
```

Remove normal product use of:

```env
GITHUB_TOKEN=
```

Keep `GITHUB_TOKEN` only if a note says it is legacy and unsupported by the GitHub App product path.

- [ ] **Step 2: Update README scope**

In `README.md`, remove the mock scenario section and add:

```markdown
### GitHub App setup

The product uses one GitHub App for user login, installation access, webhooks, Pull Request context, Git clone, comments, and commit statuses.

Configure the GitHub App with:

- Callback URL: `http://localhost:8000/api/auth/github/callback`
- Webhook URL: `{public-backend-url}/api/github/webhooks`
- Webhook secret: same value as `GITHUB_WEBHOOK_SECRET`
- Repository permissions:
  - Metadata: read
  - Contents: read
  - Pull requests: read
  - Issues or Pull requests: write for PR comments
  - Commit statuses: write
- Events:
  - Pull request
  - Installation
  - Installation repositories
  - GitHub App authorization
```

Add:

```markdown
Mock Analysis Runs are no longer supported. Analysis Runs are created only from GitHub App Pull Request events or from the Analyze action on a live GitHub Pull Request.
```

- [ ] **Step 3: Search docs for stale mock instructions**

Run:

```powershell
rg -n "mock|Mock|GITHUB_TOKEN|manual repository" README.md .env.example docs
```

Expected: no product instructions telling users to create mock analysis or use `GITHUB_TOKEN` as the normal GitHub integration path.

- [ ] **Step 4: Commit**

```powershell
git add README.md .env.example
git commit -m "docs: document github app setup"
```

---

### Task 16: Final Verification

**Files:**
- No new files unless fixing failures.

- [ ] **Step 1: Run backend tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

Expected: all tests PASS, except database-backed tests may SKIP only when PostgreSQL test DB is unavailable.

- [ ] **Step 2: Run frontend build**

Run:

```powershell
npm run build
```

Expected: PASS.

- [ ] **Step 3: Search for removed product surface**

Run:

```powershell
rg -n "MockScenario|MockAnalysisRunCreate|createMockAnalysisRun|Create Mock Analysis|analysis-runs/mock|SCENARIOS|GITHUB_TOKEN" backend frontend README.md .env.example
```

Expected:

- no `MockScenario`;
- no `MockAnalysisRunCreate`;
- no `createMockAnalysisRun`;
- no `Create Mock Analysis`;
- no `/analysis-runs/mock`;
- no `SCENARIOS`;
- `GITHUB_TOKEN` appears only in legacy notes or not at all.

- [ ] **Step 4: Inspect git status**

Run:

```powershell
git status --short
```

Expected: only intentional changes remain.

- [ ] **Step 5: Commit verification fixes**

If verification required follow-up changes, stage only files modified during this final verification task:

```powershell
git add backend/app frontend/src README.md .env.example
git commit -m "test: verify github-only multiuser flow"
```
