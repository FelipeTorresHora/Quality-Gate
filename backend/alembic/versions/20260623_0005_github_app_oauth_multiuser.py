"""github app oauth multiuser

Revision ID: 20260623_0005
Revises: 20260622_0004
Create Date: 2026-06-23
"""

from collections.abc import Sequence

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
    op.add_column(
        "users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        """
        WITH numbered AS (
            SELECT id, row_number() OVER (ORDER BY created_at, id) AS rn
            FROM users
            WHERE github_user_id IS NULL OR github_login IS NULL
        )
        UPDATE users
        SET
            github_user_id = COALESCE(users.github_user_id, -numbered.rn),
            github_login = COALESCE(users.github_login, 'legacy-user-' || numbered.rn)
        FROM numbered
        WHERE users.id = numbered.id
        """
    )
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.alter_column(
        "users",
        "github_user_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "users",
        "github_login",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "users", "name", existing_type=sa.String(length=255), nullable=True
    )
    op.alter_column(
        "users", "email", existing_type=sa.String(length=255), nullable=True
    )
    op.create_unique_constraint("uq_users_github_user_id", "users", ["github_user_id"])
    op.create_index(op.f("ix_users_github_user_id"), "users", ["github_user_id"])
    op.create_unique_constraint("uq_users_github_login", "users", ["github_login"])

    op.drop_constraint(
        "github_connections_user_id_fkey", "github_connections", type_="foreignkey"
    )
    op.add_column(
        "github_connections", sa.Column("github_user_id", sa.BigInteger(), nullable=True)
    )
    op.alter_column(
        "github_connections",
        "github_username",
        existing_type=sa.String(length=255),
        new_column_name="github_login",
        existing_nullable=False,
    )
    op.alter_column(
        "github_connections",
        "access_token_encrypted",
        existing_type=sa.String(length=2048),
        type_=sa.Text(),
        nullable=True,
    )
    op.add_column(
        "github_connections",
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
    )
    op.add_column(
        "github_connections",
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "github_connections",
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "github_connections",
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        """
        UPDATE github_connections
        SET github_user_id = users.github_user_id
        FROM users
        WHERE github_connections.user_id = users.id
            AND github_connections.github_user_id IS NULL
        """
    )
    op.alter_column(
        "github_connections",
        "github_user_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.create_index(
        op.f("ix_github_connections_github_user_id"),
        "github_connections",
        ["github_user_id"],
    )
    op.create_index(
        op.f("ix_github_connections_user_id"), "github_connections", ["user_id"]
    )
    op.create_foreign_key(
        "fk_github_connections_user_id_users",
        "github_connections",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "github_app_installations",
        sa.Column("installation_id", sa.BigInteger(), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("account_login", sa.Text(), nullable=False),
        sa.Column("account_type", sa.Text(), nullable=False),
        sa.Column("repository_selection", sa.Text(), nullable=True),
        sa.Column(
            "permissions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("events_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("installation_id"),
    )
    op.create_index(
        op.f("ix_github_app_installations_account_id"),
        "github_app_installations",
        ["account_id"],
    )
    op.create_index(
        op.f("ix_github_app_installations_installation_id"),
        "github_app_installations",
        ["installation_id"],
    )
    op.create_table(
        "user_sessions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_token_hash", sa.Text(), nullable=False),
        sa.Column("csrf_token_hash", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token_hash"),
    )
    op.create_index(op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"])
    op.create_table(
        "installation_repositories",
        sa.Column("installation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_repo_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["installation_id"], ["github_app_installations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"], ["repositories.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "installation_id", "repository_id", name="uq_installation_repository"
        ),
    )
    op.create_index(
        op.f("ix_installation_repositories_github_repo_id"),
        "installation_repositories",
        ["github_repo_id"],
    )
    op.create_index(
        op.f("ix_installation_repositories_installation_id"),
        "installation_repositories",
        ["installation_id"],
    )
    op.create_index(
        op.f("ix_installation_repositories_repository_id"),
        "installation_repositories",
        ["repository_id"],
    )
    op.create_table(
        "user_repository_access",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("installation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission", sa.Text(), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["installation_id"], ["github_app_installations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "repository_id", name="uq_user_repository_access"),
    )
    op.create_index(
        op.f("ix_user_repository_access_installation_id"),
        "user_repository_access",
        ["installation_id"],
    )
    op.create_index(
        op.f("ix_user_repository_access_repository_id"),
        "user_repository_access",
        ["repository_id"],
    )
    op.create_index(
        op.f("ix_user_repository_access_user_id"), "user_repository_access", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_user_repository_access_user_id"), table_name="user_repository_access"
    )
    op.drop_index(
        op.f("ix_user_repository_access_repository_id"),
        table_name="user_repository_access",
    )
    op.drop_index(
        op.f("ix_user_repository_access_installation_id"),
        table_name="user_repository_access",
    )
    op.drop_table("user_repository_access")
    op.drop_index(
        op.f("ix_installation_repositories_repository_id"),
        table_name="installation_repositories",
    )
    op.drop_index(
        op.f("ix_installation_repositories_installation_id"),
        table_name="installation_repositories",
    )
    op.drop_index(
        op.f("ix_installation_repositories_github_repo_id"),
        table_name="installation_repositories",
    )
    op.drop_table("installation_repositories")
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index(
        op.f("ix_github_app_installations_installation_id"),
        table_name="github_app_installations",
    )
    op.drop_index(
        op.f("ix_github_app_installations_account_id"),
        table_name="github_app_installations",
    )
    op.drop_table("github_app_installations")

    op.drop_constraint(
        "fk_github_connections_user_id_users", "github_connections", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_github_connections_user_id"), table_name="github_connections"
    )
    op.drop_index(
        op.f("ix_github_connections_github_user_id"),
        table_name="github_connections",
    )
    op.execute(
        """
        UPDATE github_connections
        SET access_token_encrypted = ''
        WHERE access_token_encrypted IS NULL
        """
    )
    op.drop_column("github_connections", "revoked_at")
    op.drop_column("github_connections", "refresh_token_expires_at")
    op.drop_column("github_connections", "access_token_expires_at")
    op.drop_column("github_connections", "refresh_token_encrypted")
    op.alter_column(
        "github_connections",
        "access_token_encrypted",
        existing_type=sa.Text(),
        type_=sa.String(length=2048),
        nullable=False,
    )
    op.alter_column(
        "github_connections",
        "github_login",
        existing_type=sa.String(length=255),
        new_column_name="github_username",
        existing_nullable=False,
    )
    op.drop_column("github_connections", "github_user_id")
    op.create_foreign_key(
        "github_connections_user_id_fkey",
        "github_connections",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint("uq_users_github_login", "users", type_="unique")
    op.drop_index(op.f("ix_users_github_user_id"), table_name="users")
    op.drop_constraint("uq_users_github_user_id", "users", type_="unique")
    op.execute(
        """
        UPDATE users
        SET name = COALESCE(name, github_login, 'Legacy User')
        WHERE name IS NULL
        """
    )
    op.execute(
        """
        UPDATE users
        SET email = COALESCE(NULLIF(email, ''), github_login, 'user')
            || '-' || substring(id::text, 1, 8)
            || '@users.noreply.github.local'
        WHERE email IS NULL
            OR email = ''
            OR id IN (
                SELECT id
                FROM (
                    SELECT
                        id,
                        row_number() OVER (PARTITION BY email ORDER BY created_at, id) AS rn
                    FROM users
                    WHERE email IS NOT NULL AND email <> ''
                ) duplicates
                WHERE duplicates.rn > 1
            )
        """
    )
    op.alter_column(
        "users", "email", existing_type=sa.String(length=255), nullable=False
    )
    op.alter_column(
        "users", "name", existing_type=sa.String(length=255), nullable=False
    )
    op.create_unique_constraint("users_email_key", "users", ["email"])
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "github_login")
    op.drop_column("users", "github_user_id")
