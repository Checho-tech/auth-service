"""Import every model here so Base.metadata is complete for Alembic autogenerate."""

from auth_service.infrastructure.database.models.audit_log import AuditLog
from auth_service.infrastructure.database.models.role import (
    Permission,
    Role,
    role_permissions,
    user_roles,
)
from auth_service.infrastructure.database.models.token import PasswordResetToken, RefreshToken
from auth_service.infrastructure.database.models.user import User

__all__ = [
    "AuditLog",
    "Permission",
    "PasswordResetToken",
    "RefreshToken",
    "Role",
    "User",
    "role_permissions",
    "user_roles",
]
