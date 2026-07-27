"""Reusable column mixins to avoid repeating id/timestamp boilerplate on every model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """UUID (not auto-increment int) primary key.

    Sequential integer IDs leak information (total user count) and enable
    IDOR-style enumeration if ever reflected in a URL or response body.
    Generated client-side (default=uuid.uuid4) so it works against any
    Postgres instance without requiring the pgcrypto/uuid-ossp extensions.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
