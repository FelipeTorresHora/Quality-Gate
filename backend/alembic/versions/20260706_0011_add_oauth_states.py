"""add oauth states

Revision ID: 20260706_0011
Revises: 20260706_0010
Create Date: 2026-07-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260706_0011"
down_revision: str | None = "20260706_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_states",
        sa.Column("state_hash", sa.Text(), nullable=False),
        sa.Column("verifier_hash", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("state_hash"),
    )
    op.create_index(op.f("ix_oauth_states_expires_at"), "oauth_states", ["expires_at"])
    op.create_index(op.f("ix_oauth_states_state_hash"), "oauth_states", ["state_hash"])


def downgrade() -> None:
    op.drop_index(op.f("ix_oauth_states_state_hash"), table_name="oauth_states")
    op.drop_index(op.f("ix_oauth_states_expires_at"), table_name="oauth_states")
    op.drop_table("oauth_states")
