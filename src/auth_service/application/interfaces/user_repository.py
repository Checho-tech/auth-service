"""Abstract contract for user persistence.

The application layer (services) depends only on this Protocol, never on
the concrete SQLAlchemy implementation. This is the Dependency Inversion
Principle: high-level modules (business logic) and low-level modules
(database access) both depend on this abstraction.
"""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from auth_service.domain.entities import UserEntity


class IUserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> UserEntity | None: ...

    async def get_by_email(self, email: str) -> UserEntity | None: ...

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[UserEntity]: ...

    async def create(
        self, email: str, hashed_password: str, full_name: str | None
    ) -> UserEntity: ...

    async def assign_roles(self, user_id: UUID, role_names: tuple[str, ...]) -> None: ...

    async def set_active(self, user_id: UUID, is_active: bool) -> None: ...

    async def update_password(self, user_id: UUID, hashed_password: str) -> None: ...

    async def set_verified(self, user_id: UUID, is_verified: bool) -> None: ...

    async def register_failed_login(
        self, user_id: UUID, failed_attempts: int, locked_until: datetime | None
    ) -> None: ...

    async def reset_failed_login(self, user_id: UUID) -> None: ...
