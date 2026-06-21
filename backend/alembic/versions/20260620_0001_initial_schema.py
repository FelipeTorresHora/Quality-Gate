"""initial schema

Revision ID: 20260620_0001
Revises:
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260620_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


analysis_run_status = postgresql.ENUM(
    "pending", "running", "completed", "error", name="analysis_run_status"
)
gate_decision = postgresql.ENUM("pass", "fail", name="gate_decision")
finding_category = postgresql.ENUM(
    "coverage", "security", "technical_debt", name="finding_category"
)
finding_severity = postgresql.ENUM(
    "low", "medium", "high", "critical", name="finding_severity"
)


def upgrade() -> None:
    bind = op.get_bind()
    analysis_run_status.create(bind, checkfirst=True)
    gate_decision.create(bind, checkfirst=True)
    finding_category.create(bind, checkfirst=True)
    finding_severity.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
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
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "repositories",
        sa.Column("github_repo_id", sa.BigInteger(), nullable=True),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=511), nullable=False),
        sa.Column("default_branch", sa.String(length=255), nullable=False),
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
        sa.UniqueConstraint("full_name"),
        sa.UniqueConstraint("github_repo_id"),
    )
    op.create_index(
        op.f("ix_repositories_full_name"), "repositories", ["full_name"], unique=False
    )
    op.create_index(
        op.f("ix_repositories_github_repo_id"),
        "repositories",
        ["github_repo_id"],
        unique=False,
    )
    op.create_table(
        "github_connections",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_username", sa.String(length=255), nullable=False),
        sa.Column("access_token_encrypted", sa.String(length=2048), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "quality_gate_configs",
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("min_total_coverage", sa.Float(), nullable=False),
        sa.Column("max_coverage_drop", sa.Float(), nullable=False),
        sa.Column("min_changed_files_coverage", sa.Float(), nullable=False),
        sa.Column("security_fail_on", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("max_function_lines", sa.Integer(), nullable=False),
        sa.Column("max_complexity", sa.Integer(), nullable=False),
        sa.Column("fail_on_new_todo", sa.Boolean(), nullable=False),
        sa.Column("comment_on_github", sa.Boolean(), nullable=False),
        sa.Column("publish_github_status", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id"),
    )
    op.create_index(
        op.f("ix_quality_gate_configs_repository_id"),
        "quality_gate_configs",
        ["repository_id"],
        unique=False,
    )
    op.create_table(
        "analysis_runs",
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("head_sha", sa.Text(), nullable=False),
        sa.Column("status", analysis_run_status, nullable=False),
        sa.Column("decision", gate_decision, nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("coverage_result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("security_result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "technical_debt_result_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("final_report_markdown", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_analysis_runs_repository_id"),
        "analysis_runs",
        ["repository_id"],
        unique=False,
    )
    op.create_table(
        "analysis_findings",
        sa.Column("analysis_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", finding_category, nullable=False),
        sa.Column("severity", finding_severity, nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("blocking", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_analysis_findings_analysis_run_id"),
        "analysis_findings",
        ["analysis_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_findings_analysis_run_id"), table_name="analysis_findings")
    op.drop_table("analysis_findings")
    op.drop_index(op.f("ix_analysis_runs_repository_id"), table_name="analysis_runs")
    op.drop_table("analysis_runs")
    op.drop_index(op.f("ix_quality_gate_configs_repository_id"), table_name="quality_gate_configs")
    op.drop_table("quality_gate_configs")
    op.drop_table("github_connections")
    op.drop_index(op.f("ix_repositories_github_repo_id"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_full_name"), table_name="repositories")
    op.drop_table("repositories")
    op.drop_table("users")

    bind = op.get_bind()
    finding_severity.drop(bind, checkfirst=True)
    finding_category.drop(bind, checkfirst=True)
    gate_decision.drop(bind, checkfirst=True)
    analysis_run_status.drop(bind, checkfirst=True)
