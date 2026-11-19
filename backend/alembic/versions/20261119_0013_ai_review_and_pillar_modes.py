"""ai review and pillar modes

Revision ID: 20261119_0013
Revises: 20260919_0012
Create Date: 2026-11-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261119_0013"
down_revision: str | None = "20260919_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Native Postgres enums. create_type=False so add_column does not emit a second
# CREATE TYPE; upgrade() creates each type once. finding_category already exists
# and only gains the code_review label. Autogenerate did not emit that ALTER TYPE,
# and it also proposed unrelated unique-index rewrites that are not part of this change.
finding_source = postgresql.ENUM(
    "deterministic",
    "ai",
    name="finding_source",
    create_type=False,
)
gate_evaluation_mode = postgresql.ENUM(
    "hybrid",
    "deterministic",
    "ai_only",
    name="gate_evaluation_mode",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("ALTER TYPE finding_category ADD VALUE IF NOT EXISTS 'code_review'")
    finding_source.create(bind, checkfirst=True)
    gate_evaluation_mode.create(bind, checkfirst=True)
    op.add_column(
        "analysis_findings",
        sa.Column(
            "source",
            finding_source,
            nullable=False,
            server_default="deterministic",
        ),
    )
    op.add_column(
        "analysis_findings",
        sa.Column("confidence", sa.Float(), nullable=True),
    )
    op.add_column(
        "analysis_findings",
        sa.Column("suggestion_code", sa.Text(), nullable=True),
    )
    op.add_column(
        "quality_gate_configs",
        sa.Column(
            "code_review_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "quality_gate_configs",
        sa.Column(
            "coverage_mode",
            gate_evaluation_mode,
            nullable=False,
            server_default="hybrid",
        ),
    )
    op.add_column(
        "quality_gate_configs",
        sa.Column(
            "security_mode",
            gate_evaluation_mode,
            nullable=False,
            server_default="hybrid",
        ),
    )
    op.add_column(
        "quality_gate_configs",
        sa.Column(
            "technical_debt_mode",
            gate_evaluation_mode,
            nullable=False,
            server_default="hybrid",
        ),
    )


def downgrade() -> None:
    op.drop_column("quality_gate_configs", "technical_debt_mode")
    op.drop_column("quality_gate_configs", "security_mode")
    op.drop_column("quality_gate_configs", "coverage_mode")
    op.drop_column("quality_gate_configs", "code_review_enabled")
    op.drop_column("analysis_findings", "suggestion_code")
    op.drop_column("analysis_findings", "confidence")
    op.drop_column("analysis_findings", "source")
    bind = op.get_bind()
    gate_evaluation_mode.drop(bind, checkfirst=True)
    finding_source.drop(bind, checkfirst=True)
    # PostgreSQL cannot drop a single enum label. finding_category keeps code_review.
