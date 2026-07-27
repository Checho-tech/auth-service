"""Pure domain representation of a User.

Deliberately NOT a SQLAlchemy model: this is what the application/service
layer works with, so business logic never touches an ORM session or lazy-
loading proxy. Repositories are responsible for converting to/from the
persistence model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserEntity:
    id: UUID
    email: str
    hashed_password: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    failed_login_attempts: int
    locked_until: datetime | None
    role_names: tuple[str, ...] = field(default_factory=tuple)
    permission_codes: frozenset[str] = field(default_factory=frozenset)

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > now

    def has_permission(self, permission_code: str) -> bool:
        return permission_code in self.permission_codes
