"""add coverage working directory

Revision ID: 20260630_0008
Revises: 20260629_0007
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260630_0008"
down_revision: str | None = "20260629_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "coverage_execution_configs",
        sa.Column(
            "working_directory",
            sa.Text(),
            nullable=False,
            server_default=".",
        ),
    )
    op.alter_column(
        "coverage_execution_configs",
        "working_directory",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("coverage_execution_configs", "working_directory")
