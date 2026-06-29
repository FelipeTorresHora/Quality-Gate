"""add gate enable flags

Revision ID: 20260629_0007
Revises: 20260623_0006
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260629_0007"
down_revision: str | None = "20260623_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "quality_gate_configs",
        sa.Column(
            "coverage_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "quality_gate_configs",
        sa.Column(
            "security_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "quality_gate_configs",
        sa.Column(
            "technical_debt_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.alter_column("quality_gate_configs", "coverage_enabled", server_default=None)
    op.alter_column("quality_gate_configs", "security_enabled", server_default=None)
    op.alter_column(
        "quality_gate_configs", "technical_debt_enabled", server_default=None
    )


def downgrade() -> None:
    op.drop_column("quality_gate_configs", "technical_debt_enabled")
    op.drop_column("quality_gate_configs", "security_enabled")
    op.drop_column("quality_gate_configs", "coverage_enabled")
