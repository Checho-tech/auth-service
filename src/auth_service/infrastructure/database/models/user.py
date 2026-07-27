"""User model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auth_service.infrastructure.database.base import Base
from auth_service.infrastructure.database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from auth_service.infrastructure.database.models.role import Role, user_roles


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    # NULL = not locked. A timestamp in the future = locked until then.
    # Using a timestamp instead of a boolean means the account self-unlocks
    # once it expires, with no cron job or manual admin action required.
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list[Role]] = relationship(secondary=user_roles, back_populates="users")
