"""remove mock analysis

Revision ID: 20260623_0006
Revises: 20260623_0005
Create Date: 2026-06-23
"""

from collections.abc import Sequence

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
    op.execute(
        "ALTER TYPE analysis_trigger_source RENAME TO analysis_trigger_source_old"
    )
    op.execute(
        "CREATE TYPE analysis_trigger_source AS ENUM ('manual', 'github_webhook')"
    )
    op.execute(
        """
        ALTER TABLE analysis_runs
        ALTER COLUMN trigger_source TYPE analysis_trigger_source
        USING trigger_source::text::analysis_trigger_source
        """
    )
    op.execute("DROP TYPE analysis_trigger_source_old")


def downgrade() -> None:
    op.execute(
        "ALTER TYPE analysis_trigger_source RENAME TO analysis_trigger_source_old"
    )
    op.execute(
        "CREATE TYPE analysis_trigger_source AS ENUM "
        "('mock', 'manual', 'github_webhook')"
    )
    op.execute(
        """
        ALTER TABLE analysis_runs
        ALTER COLUMN trigger_source TYPE analysis_trigger_source
        USING trigger_source::text::analysis_trigger_source
        """
    )
    op.execute("DROP TYPE analysis_trigger_source_old")
