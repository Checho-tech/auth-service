"""Audit log model.

Append-only by convention: the application layer only ever INSERTs here,
never UPDATEs or DELETEs. In a real production deployment this should also
be enforced at the database-permission level (REVOKE UPDATE, DELETE ON
audit_logs FROM app_role), which we document as a follow-up in the README.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from auth_service.infrastructure.database.base import Base
from auth_service.infrastructure.database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    # Nullable: e.g. a login attempt with an email that doesn't exist has no user to attach to.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))  # long enough for IPv6
    user_agent: Mapped[str | None] = mapped_column(String(255))
    event_metadata: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    # Overrides TimestampMixin.created_at to add an index: audit logs are
    # frequently queried by time range (e.g. "events in the last 24h").
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
