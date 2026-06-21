from uuid import UUID

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import FindingCategory, FindingSeverity
from app.models.mixins import UUIDPrimaryKeyMixin


def enum_values(enum_cls):
    return [member.value for member in enum_cls]


class AnalysisFinding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "analysis_findings"

    analysis_run_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[FindingCategory] = mapped_column(
        Enum(
            FindingCategory,
            name="finding_category",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(
            FindingSeverity,
            name="finding_severity",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
    )
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    blocking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    analysis_run: Mapped["AnalysisRun"] = relationship(back_populates="findings")
