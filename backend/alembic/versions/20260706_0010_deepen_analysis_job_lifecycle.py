"""deepen analysis job lifecycle

Revision ID: 20260706_0010
Revises: 20260630_0009
Create Date: 2026-07-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260706_0010"
down_revision: str | None = "20260630_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "analysis_jobs",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "analysis_jobs", sa.Column("last_error", sa.Text(), nullable=True)
    )
    op.add_column(
        "analysis_jobs",
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "analysis_jobs", sa.Column("locked_by", sa.Text(), nullable=True)
    )
    op.alter_column("analysis_jobs", "attempt_count", server_default=None)
    op.create_index(
        "ix_analysis_jobs_status_created_at",
        "analysis_jobs",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_analysis_jobs_status_locked_at",
        "analysis_jobs",
        ["status", "locked_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_analysis_jobs_status_locked_at", table_name="analysis_jobs")
    op.drop_index(
        "ix_analysis_jobs_status_created_at", table_name="analysis_jobs"
    )
    op.drop_column("analysis_jobs", "locked_by")
    op.drop_column("analysis_jobs", "locked_at")
    op.drop_column("analysis_jobs", "last_error")
    op.drop_column("analysis_jobs", "finished_at")
    op.drop_column("analysis_jobs", "attempt_count")
