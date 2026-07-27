"""Concrete SQLAlchemy implementation of IPasswordResetRepository."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.application.interfaces.password_reset_repository import StoredPasswordResetToken
from auth_service.infrastructure.database.models.token import PasswordResetToken


class SQLAlchemyPasswordResetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self._session.add(
            PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        )
        await self._session.commit()

    async def get_by_hash(self, token_hash: str) -> StoredPasswordResetToken | None:
        stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return StoredPasswordResetToken(
            user_id=row.user_id, expires_at=row.expires_at, used_at=row.used_at
        )

    async def mark_used(self, token_hash: str) -> None:
        await self._session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
            .values(used_at=datetime.now(UTC))
        )
        await self._session.commit()
