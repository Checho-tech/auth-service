"""Concrete SQLAlchemy implementation of IAuditLogRepository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.application.interfaces.audit_log_repository import StoredAuditLogEntry
from auth_service.infrastructure.database.models.audit_log import AuditLog


class SQLAlchemyAuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log_event(
        self,
        event_type: str,
        user_id: UUID | None,
        ip_address: str | None,
        user_agent: str | None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self._session.add(
            AuditLog(
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                event_metadata=metadata,
            )
        )
        await self._session.commit()

    async def list_recent(self, limit: int = 100) -> list[StoredAuditLogEntry]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            StoredAuditLogEntry(
                id=row.id,
                event_type=row.event_type,
                user_id=row.user_id,
                ip_address=row.ip_address,
                user_agent=row.user_agent,
                metadata=row.event_metadata,
                created_at=row.created_at,
            )
            for row in rows
        ]
