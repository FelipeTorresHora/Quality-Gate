from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AnalysisJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analysis_jobs"

    analysis_run_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="queued")
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    locked_by: Mapped[str | None] = mapped_column(Text, nullable=True)
