"""Concrete SQLAlchemy implementation of IRefreshTokenRepository."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.application.interfaces.refresh_token_repository import StoredRefreshToken
from auth_service.infrastructure.database.models.token import RefreshToken


class SQLAlchemyRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, user_id: UUID, token_hash: str, expires_at: datetime, user_agent: str | None
    ) -> None:
        self._session.add(
            RefreshToken(
                user_id=user_id, token_hash=token_hash, expires_at=expires_at, user_agent=user_agent
            )
        )
        await self._session.commit()

    async def get_by_hash(self, token_hash: str) -> StoredRefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return StoredRefreshToken(
            user_id=row.user_id, expires_at=row.expires_at, revoked_at=row.revoked_at
        )

    async def revoke(self, token_hash: str) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.commit()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.commit()
