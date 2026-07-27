"""Concrete SQLAlchemy implementation of IUserRepository.

Converts between the persistence model (`models.User`, an SQLAlchemy ORM
object tied to a DB session) and the domain entity (`UserEntity`, a plain
dataclass) — this is the one place that translation happens, so the rest
of the app never touches an ORM object directly.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth_service.domain.entities import UserEntity
from auth_service.infrastructure.database.models.role import Role
from auth_service.infrastructure.database.models.user import User

# Loads User -> roles -> permissions in one round trip, so authorization
# checks (Fase 4) never need a second query per request.
_WITH_ROLES_AND_PERMISSIONS = selectinload(User.roles).selectinload(Role.permissions)


def _to_entity(user: User) -> UserEntity:
    return UserEntity(
        id=user.id,
        email=user.email,
        hashed_password=user.hashed_password,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=user.locked_until,
        role_names=tuple(role.name for role in user.roles),
        permission_codes=frozenset(
            permission.code for role in user.roles for permission in role.permissions
        ),
    )


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> UserEntity | None:
        stmt = select(User).where(User.id == user_id).options(_WITH_ROLES_AND_PERMISSIONS)
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(user) if user else None

    async def get_by_email(self, email: str) -> UserEntity | None:
        stmt = select(User).where(User.email == email).options(_WITH_ROLES_AND_PERMISSIONS)
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(user) if user else None

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[UserEntity]:
        stmt = (
            select(User)
            .options(_WITH_ROLES_AND_PERMISSIONS)
            .order_by(User.created_at)
            .offset(offset)
            .limit(limit)
        )
        users = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(user) for user in users]

    async def create(self, email: str, hashed_password: str, full_name: str | None) -> UserEntity:
        default_role = (
            await self._session.execute(select(Role).where(Role.name == "employee"))
        ).scalar_one_or_none()

        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            roles=[default_role] if default_role else [],
        )
        self._session.add(user)
        await self._session.commit()
        # Re-fetch with the full roles->permissions tree rather than
        # `session.refresh`, which would only reload `roles`, not the
        # nested `permissions` collection needed by `_to_entity`.
        return await self.get_by_id(user.id)  # type: ignore[return-value]

    async def assign_roles(self, user_id: UUID, role_names: tuple[str, ...]) -> None:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        user = (await self._session.execute(stmt)).scalar_one_or_none()
        if user is None:
            return
        roles = (
            (await self._session.execute(select(Role).where(Role.name.in_(role_names))))
            .scalars()
            .all()
        )
        user.roles = list(roles)
        await self._session.commit()

    async def set_active(self, user_id: UUID, is_active: bool) -> None:
        user = await self._session.get(User, user_id)
        if user is None:
            return
        user.is_active = is_active
        await self._session.commit()

    async def update_password(self, user_id: UUID, hashed_password: str) -> None:
        user = await self._session.get(User, user_id)
        if user is None:
            return
        user.hashed_password = hashed_password
        await self._session.commit()

    async def set_verified(self, user_id: UUID, is_verified: bool) -> None:
        user = await self._session.get(User, user_id)
        if user is None:
            return
        user.is_verified = is_verified
        await self._session.commit()

    async def register_failed_login(
        self, user_id: UUID, failed_attempts: int, locked_until: datetime | None
    ) -> None:
        user = await self._session.get(User, user_id)
        if user is None:
            return
        user.failed_login_attempts = failed_attempts
        user.locked_until = locked_until
        await self._session.commit()

    async def reset_failed_login(self, user_id: UUID) -> None:
        user = await self._session.get(User, user_id)
        if user is None:
            return
        user.failed_login_attempts = 0
        user.locked_until = None
        await self._session.commit()
