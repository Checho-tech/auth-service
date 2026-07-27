"""Abstract contract for password reset token persistence."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class StoredPasswordResetToken:
    user_id: UUID
    expires_at: datetime
    used_at: datetime | None


class IPasswordResetRepository(Protocol):
    async def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None: ...

    async def get_by_hash(self, token_hash: str) -> StoredPasswordResetToken | None: ...

    async def mark_used(self, token_hash: str) -> None: ...
