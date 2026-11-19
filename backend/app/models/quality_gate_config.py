from uuid import UUID

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, false
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import GateEvaluationMode
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


def enum_values(enum_cls):
    return [member.value for member in enum_cls]


_gate_evaluation_mode = Enum(
    GateEvaluationMode,
    name="gate_evaluation_mode",
    values_callable=enum_values,
    native_enum=True,
)


class QualityGateConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quality_gate_configs"

    repository_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    min_total_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=80)
    max_coverage_drop: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    min_changed_files_coverage: Mapped[float] = mapped_column(
        Float, nullable=False, default=75
    )
    coverage_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    security_fail_on: Mapped[list[str] | dict] = mapped_column(
        JSONB, nullable=False, default=lambda: ["critical", "high"]
    )
    security_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_function_lines: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    max_complexity: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    fail_on_new_todo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    technical_debt_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    # Off until a repository opts into the code review pillar.
    code_review_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    # hybrid: deterministic gate still owns Gate Decision; AI findings stay non-blocking.
    coverage_mode: Mapped[GateEvaluationMode] = mapped_column(
        _gate_evaluation_mode,
        nullable=False,
        default=GateEvaluationMode.HYBRID,
        server_default=GateEvaluationMode.HYBRID.value,
    )
    security_mode: Mapped[GateEvaluationMode] = mapped_column(
        _gate_evaluation_mode,
        nullable=False,
        default=GateEvaluationMode.HYBRID,
        server_default=GateEvaluationMode.HYBRID.value,
    )
    technical_debt_mode: Mapped[GateEvaluationMode] = mapped_column(
        _gate_evaluation_mode,
        nullable=False,
        default=GateEvaluationMode.HYBRID,
        server_default=GateEvaluationMode.HYBRID.value,
    )
    comment_on_github: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    publish_github_status: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    repository: Mapped["Repository"] = relationship(back_populates="quality_gate_config")
