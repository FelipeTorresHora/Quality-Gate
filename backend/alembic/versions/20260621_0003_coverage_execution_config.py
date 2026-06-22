"""coverage execution config

Revision ID: 20260621_0003
Revises: 20260621_0002
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260621_0003"
down_revision: str | None = "20260621_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


coverage_language = postgresql.ENUM(
    "python", "typescript", "javascript", "go", name="coverage_language"
)
coverage_report_format = postgresql.ENUM(
    "cobertura_xml", "lcov", "go_coverprofile", name="coverage_report_format"
)


def upgrade() -> None:
    bind = op.get_bind()
    coverage_language.create(bind, checkfirst=True)
    coverage_report_format.create(bind, checkfirst=True)

    op.create_table(
        "coverage_execution_configs",
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", coverage_language, nullable=False),
        sa.Column("install_command", sa.Text(), nullable=False),
        sa.Column("test_command", sa.Text(), nullable=False),
        sa.Column("report_path", sa.Text(), nullable=False),
        sa.Column("report_format", coverage_report_format, nullable=False),
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
            ["repository_id"], ["repositories.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id"),
    )
    op.create_index(
        op.f("ix_coverage_execution_configs_repository_id"),
        "coverage_execution_configs",
        ["repository_id"],
        unique=False,
    )
    op.execute(
        """
        INSERT INTO coverage_execution_configs (
            repository_id,
            language,
            install_command,
            test_command,
            report_path,
            report_format,
            id
        )
        SELECT
            repositories.id,
            'python',
            'pip install -r requirements.txt',
            'pytest --cov=. --cov-report=xml:coverage.xml',
            'coverage.xml',
            'cobertura_xml',
            gen_random_uuid()
        FROM repositories
        WHERE NOT EXISTS (
            SELECT 1
            FROM coverage_execution_configs
            WHERE coverage_execution_configs.repository_id = repositories.id
        )
        """
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_coverage_execution_configs_repository_id"),
        table_name="coverage_execution_configs",
    )
    op.drop_table("coverage_execution_configs")

    bind = op.get_bind()
    coverage_report_format.drop(bind, checkfirst=True)
    coverage_language.drop(bind, checkfirst=True)
