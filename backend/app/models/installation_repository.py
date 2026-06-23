from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InstallationRepository(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "installation_repositories"
    __table_args__ = (
        UniqueConstraint(
            "installation_id", "repository_id", name="uq_installation_repository"
        ),
    )

    installation_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("github_app_installations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repository_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_repo_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)

    installation: Mapped["GitHubAppInstallation"] = relationship(
        back_populates="repositories"
    )
    repository: Mapped["Repository"] = relationship()
