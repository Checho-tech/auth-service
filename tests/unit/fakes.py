"""In-memory fake implementations of the application/interfaces Protocols.

These exist ONLY for tests. They satisfy the same structural interface
(IUserRepository, IRefreshTokenRepository, etc.) as the real SQLAlchemy
repositories, which is exactly what makes AuthService testable without a
database: the service depends on the Protocol, not on any specific
implementation, so swapping one in for the other is free.
"""

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from auth_service.application.interfaces.audit_log_repository import StoredAuditLogEntry
from auth_service.application.interfaces.password_reset_repository import StoredPasswordResetToken
from auth_service.application.interfaces.refresh_token_repository import StoredRefreshToken
from auth_service.domain.entities import UserEntity

# Mirrors the role -> permission seed data from the Alembic seed migration,
# just enough for unit tests that exercise role assignment.
_ROLE_PERMISSIONS = {
    "admin": {"users:read", "users:write", "users:delete", "roles:manage", "audit:read"},
    "manager": {"users:read", "users:write", "audit:read"},
    "employee": {"users:read"},
}


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[UUID, UserEntity] = {}

    async def get_by_id(self, user_id: UUID) -> UserEntity | None:
        return self.users.get(user_id)

    async def get_by_email(self, email: str) -> UserEntity | None:
        return next((u for u in self.users.values() if u.email == email), None)

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[UserEntity]:
        return list(self.users.values())[offset : offset + limit]

    async def create(self, email: str, hashed_password: str, full_name: str | None) -> UserEntity:
        user = UserEntity(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_verified=False,
            failed_login_attempts=0,
            locked_until=None,
            role_names=("employee",),
            permission_codes=frozenset({"users:read"}),
        )
        self.users[user.id] = user
        return user

    async def assign_roles(self, user_id: UUID, role_names: tuple[str, ...]) -> None:
        permission_codes = frozenset().union(*(_ROLE_PERMISSIONS.get(r, set()) for r in role_names))
        self.users[user_id] = replace(self.users[user_id], role_names=role_names, permission_codes=permission_codes)

    async def set_active(self, user_id: UUID, is_active: bool) -> None:
        self.users[user_id] = replace(self.users[user_id], is_active=is_active)

    async def update_password(self, user_id: UUID, hashed_password: str) -> None:
        self.users[user_id] = replace(self.users[user_id], hashed_password=hashed_password)

    async def set_verified(self, user_id: UUID, is_verified: bool) -> None:
        self.users[user_id] = replace(self.users[user_id], is_verified=is_verified)

    async def register_failed_login(
        self, user_id: UUID, failed_attempts: int, locked_until: datetime | None
    ) -> None:
        self.users[user_id] = replace(
            self.users[user_id], failed_login_attempts=failed_attempts, locked_until=locked_until
        )

    async def reset_failed_login(self, user_id: UUID) -> None:
        self.users[user_id] = replace(self.users[user_id], failed_login_attempts=0, locked_until=None)


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self._tokens: dict[str, StoredRefreshToken] = {}

    async def create(
        self, user_id: UUID, token_hash: str, expires_at: datetime, user_agent: str | None
    ) -> None:
        self._tokens[token_hash] = StoredRefreshToken(user_id=user_id, expires_at=expires_at, revoked_at=None)

    async def get_by_hash(self, token_hash: str) -> StoredRefreshToken | None:
        return self._tokens.get(token_hash)

    async def revoke(self, token_hash: str) -> None:
        if token_hash in self._tokens:
            stored = self._tokens[token_hash]
            self._tokens[token_hash] = replace(stored, revoked_at=datetime.now(UTC))

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        for token_hash, stored in self._tokens.items():
            if stored.user_id == user_id and stored.revoked_at is None:
                self._tokens[token_hash] = replace(stored, revoked_at=datetime.now(UTC))


class FakePasswordResetRepository:
    def __init__(self) -> None:
        self._tokens: dict[str, StoredPasswordResetToken] = {}

    async def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self._tokens[token_hash] = StoredPasswordResetToken(user_id=user_id, expires_at=expires_at, used_at=None)

    async def get_by_hash(self, token_hash: str) -> StoredPasswordResetToken | None:
        return self._tokens.get(token_hash)

    async def mark_used(self, token_hash: str) -> None:
        stored = self._tokens[token_hash]
        self._tokens[token_hash] = replace(stored, used_at=datetime.now(UTC))


class FakeAuditLogRepository:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def log_event(
        self,
        event_type: str,
        user_id: UUID | None,
        ip_address: str | None,
        user_agent: str | None,
        metadata: dict | None = None,
    ) -> None:
        self.events.append({"event_type": event_type, "user_id": user_id, "metadata": metadata})

    async def list_recent(self, limit: int = 100) -> list[StoredAuditLogEntry]:
        return [
            StoredAuditLogEntry(
                id=uuid.uuid4(),
                event_type=e["event_type"],
                user_id=e["user_id"],
                ip_address=None,
                user_agent=None,
                metadata=e["metadata"],
                created_at=datetime.now(UTC),
            )
            for e in self.events[-limit:]
        ]


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})
