"""Abstract contract for writing and reading audit trail entries."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StoredAuditLogEntry:
    id: UUID
    event_type: str
    user_id: UUID | None
    ip_address: str | None
    user_agent: str | None
    metadata: dict[str, object] | None
    created_at: datetime


class IAuditLogRepository(Protocol):
    async def log_event(
        self,
        event_type: str,
        user_id: UUID | None,
        ip_address: str | None,
        user_agent: str | None,
        metadata: dict[str, object] | None = None,
    ) -> None: ...

    async def list_recent(self, limit: int = 100) -> list[StoredAuditLogEntry]: ...
