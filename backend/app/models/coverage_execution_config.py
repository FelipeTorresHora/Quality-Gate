from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CoverageLanguage, CoverageReportFormat
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


def enum_values(enum_cls):
    return [member.value for member in enum_cls]


class CoverageExecutionConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "coverage_execution_configs"

    repository_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    language: Mapped[CoverageLanguage] = mapped_column(
        Enum(
            CoverageLanguage,
            name="coverage_language",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        default=CoverageLanguage.PYTHON,
    )
    install_command: Mapped[str] = mapped_column(
        Text, nullable=False, default="pip install -r requirements.txt"
    )
    test_command: Mapped[str] = mapped_column(
        Text, nullable=False, default="pytest --cov=. --cov-report=xml:coverage.xml"
    )
    report_path: Mapped[str] = mapped_column(
        Text, nullable=False, default="coverage.xml"
    )
    report_format: Mapped[CoverageReportFormat] = mapped_column(
        Enum(
            CoverageReportFormat,
            name="coverage_report_format",
            values_callable=enum_values,
            native_enum=True,
        ),
        nullable=False,
        default=CoverageReportFormat.COBERTURA_XML,
    )

    repository: Mapped["Repository"] = relationship(
        back_populates="coverage_execution_config"
    )
