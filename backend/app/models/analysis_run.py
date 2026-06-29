from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AnalysisRunStatus, AnalysisTriggerSource, GateDecision
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


def enum_values(enum_cls):
    return [member.value for member in enum_cls]


class AnalysisRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "pr_number",
            "head_sha",
            name="uq_analysis_runs_repository_pr_head_sha",
        ),
    )

    repository_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    head_sha: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AnalysisRunStatus] = mapped_column(
        Enum(
            AnalysisRunStatus,
            name="analysis_run_status",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        default=AnalysisRunStatus.PENDING,
    )
    decision: Mapped[GateDecision | None] = mapped_column(
        Enum(
            GateDecision,
            name="gate_decision",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=True,
    )
    trigger_source: Mapped[AnalysisTriggerSource] = mapped_column(
        Enum(
            AnalysisTriggerSource,
            name="analysis_trigger_source",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        default=AnalysisTriggerSource.MOCK,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_result_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    security_result_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    technical_debt_result_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    ai_review_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    pull_request_snapshot_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    changed_files_snapshot_json: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
    diff_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_truncated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    final_report_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    repository: Mapped["Repository"] = relationship(back_populates="analysis_runs")
    findings: Mapped[list["AnalysisFinding"]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
