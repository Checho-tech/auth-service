"""Abstract contract for refresh token persistence (needed for revocation)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StoredRefreshToken:
    user_id: UUID
    expires_at: datetime
    revoked_at: datetime | None


class IRefreshTokenRepository(Protocol):
    async def create(
        self, user_id: UUID, token_hash: str, expires_at: datetime, user_agent: str | None
    ) -> None: ...

    async def get_by_hash(self, token_hash: str) -> StoredRefreshToken | None: ...

    async def revoke(self, token_hash: str) -> None: ...

    async def revoke_all_for_user(self, user_id: UUID) -> None: ...
