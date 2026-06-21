"""github pr context trigger

Revision ID: 20260621_0002
Revises: 20260620_0001
Create Date: 2026-06-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260621_0002"
down_revision: str | None = "20260620_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


analysis_trigger_source = postgresql.ENUM(
    "mock", "manual", "github_webhook", name="analysis_trigger_source"
)


def upgrade() -> None:
    bind = op.get_bind()
    analysis_trigger_source.create(bind, checkfirst=True)

    op.add_column(
        "analysis_runs",
        sa.Column(
            "trigger_source",
            analysis_trigger_source,
            nullable=False,
            server_default="mock",
        ),
    )
    op.add_column(
        "analysis_runs",
        sa.Column(
            "pull_request_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "analysis_runs",
        sa.Column(
            "changed_files_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "analysis_runs",
        sa.Column("diff_snapshot", sa.Text(), nullable=True),
    )
    op.add_column(
        "analysis_runs",
        sa.Column(
            "diff_truncated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_unique_constraint(
        "uq_analysis_runs_repository_pr_head_sha",
        "analysis_runs",
        ["repository_id", "pr_number", "head_sha"],
    )

    op.alter_column("analysis_runs", "trigger_source", server_default=None)
    op.alter_column("analysis_runs", "pull_request_snapshot_json", server_default=None)
    op.alter_column("analysis_runs", "changed_files_snapshot_json", server_default=None)
    op.alter_column("analysis_runs", "diff_truncated", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "uq_analysis_runs_repository_pr_head_sha",
        "analysis_runs",
        type_="unique",
    )
    op.drop_column("analysis_runs", "diff_truncated")
    op.drop_column("analysis_runs", "diff_snapshot")
    op.drop_column("analysis_runs", "changed_files_snapshot_json")
    op.drop_column("analysis_runs", "pull_request_snapshot_json")
    op.drop_column("analysis_runs", "trigger_source")

    bind = op.get_bind()
    analysis_trigger_source.drop(bind, checkfirst=True)
