from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Repository(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "repositories"

    github_repo_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, unique=True, index=True
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(
        String(511), nullable=False, unique=True, index=True
    )
    default_branch: Mapped[str] = mapped_column(String(255), nullable=False)

    quality_gate_config: Mapped["QualityGateConfig"] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )
    coverage_execution_config: Mapped["CoverageExecutionConfig"] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
