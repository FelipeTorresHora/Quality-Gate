"""add coverage language preset confirmed

Revision ID: 20260919_0012
Revises: 20260706_0011
Create Date: 2026-09-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_0012"
down_revision: str | None = "20260706_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "coverage_execution_configs",
        sa.Column(
            "language_preset_confirmed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.alter_column(
        "coverage_execution_configs",
        "language_preset_confirmed",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("coverage_execution_configs", "language_preset_confirmed")
