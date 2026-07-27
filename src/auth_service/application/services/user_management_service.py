"""UserManagementService: administrative operations on user accounts.

Kept separate from AuthService on purpose (Single Responsibility Principle):
AuthService owns the identity/session lifecycle (register, login, tokens).
This service owns admin actions on *other* users' accounts (listing,
assigning roles, deactivating) — a different actor, a different set of
callers, and a different set of permissions guarding it.
"""

from uuid import UUID

from auth_service.application.interfaces import IAuditLogRepository, IUserRepository
from auth_service.application.interfaces.audit_log_repository import StoredAuditLogEntry
from auth_service.domain.entities import UserEntity
from auth_service.domain.exceptions import InvalidTokenError


class UserManagementService:
    def __init__(self, user_repo: IUserRepository, audit_log_repo: IAuditLogRepository) -> None:
        self._users = user_repo
        self._audit = audit_log_repo

    async def list_users(self, offset: int = 0, limit: int = 50) -> list[UserEntity]:
        return await self._users.list_all(offset=offset, limit=limit)

    async def assign_roles(
        self, actor_id: UUID, target_user_id: UUID, role_names: tuple[str, ...]
    ) -> UserEntity:
        target = await self._users.get_by_id(target_user_id)
        if target is None:
            raise InvalidTokenError("Target user does not exist.")

        await self._users.assign_roles(target_user_id, role_names)
        await self._audit.log_event(
            "roles_assigned",
            actor_id,
            None,
            None,
            metadata={"target_user_id": str(target_user_id), "roles": list(role_names)},
        )
        return await self._users.get_by_id(target_user_id)  # type: ignore[return-value]

    async def deactivate_user(self, actor_id: UUID, target_user_id: UUID) -> None:
        await self._users.set_active(target_user_id, is_active=False)
        await self._audit.log_event(
            "user_deactivated",
            actor_id,
            None,
            None,
            metadata={"target_user_id": str(target_user_id)},
        )

    async def list_audit_logs(self, limit: int = 100) -> list[StoredAuditLogEntry]:
        return await self._audit.list_recent(limit=limit)
