from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GitHubAppInstallation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "github_app_installations"

    installation_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True, index=True
    )
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    account_login: Mapped[str] = mapped_column(Text, nullable=False)
    account_type: Mapped[str] = mapped_column(Text, nullable=False)
    repository_selection: Mapped[str | None] = mapped_column(Text, nullable=True)
    permissions_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    events_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    suspended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    repositories: Mapped[list["InstallationRepository"]] = relationship(
        back_populates="installation",
        cascade="all, delete-orphan",
    )
    user_access: Mapped[list["UserRepositoryAccess"]] = relationship(
        back_populates="installation",
        cascade="all, delete-orphan",
    )
