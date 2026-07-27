"""FastAPI dependency-injection wiring.

Every dependency here builds a request-scoped instance from abstractions.
Routers never import a concrete repository or SQLAlchemy directly — they
ask for `AuthService` via `Depends(get_auth_service)` and let FastAPI's DI
container assemble the whole graph.
"""

from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.application.services.auth_service import AuthService
from auth_service.application.services.user_management_service import UserManagementService
from auth_service.domain.entities import UserEntity
from auth_service.domain.exceptions import InvalidTokenError
from auth_service.infrastructure.config import Settings, get_settings
from auth_service.infrastructure.database.repositories.audit_log_repository import (
    SQLAlchemyAuditLogRepository,
)
from auth_service.infrastructure.database.repositories.password_reset_repository import (
    SQLAlchemyPasswordResetRepository,
)
from auth_service.infrastructure.database.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)
from auth_service.infrastructure.database.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from auth_service.infrastructure.database.session import get_db
from auth_service.infrastructure.email.console_email_sender import ConsoleEmailSender
from auth_service.infrastructure.security.jwt_handler import decode_token

_bearer_scheme = HTTPBearer(auto_error=True)


async def get_auth_service(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(
        user_repo=SQLAlchemyUserRepository(session),
        refresh_token_repo=SQLAlchemyRefreshTokenRepository(session),
        password_reset_repo=SQLAlchemyPasswordResetRepository(session),
        audit_log_repo=SQLAlchemyAuditLogRepository(session),
        email_sender=ConsoleEmailSender(),
        settings=settings,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserEntity:
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await auth_service.get_profile(UUID(payload["sub"]))
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive.")
    return user


async def get_user_management_service(
    session: AsyncSession = Depends(get_db),
) -> UserManagementService:
    return UserManagementService(
        user_repo=SQLAlchemyUserRepository(session),
        audit_log_repo=SQLAlchemyAuditLogRepository(session),
    )


def require_permission(permission_code: str) -> Callable[[UserEntity], Awaitable[UserEntity]]:
    """Dependency factory: protects a route behind a specific permission code.

    Usage: `Depends(require_permission("users:write"))`. Checks
    `current_user.permission_codes`, which the repository loaded fresh from
    the DB in this same request (see `get_current_user`) — so revoking a
    permission from a role takes effect on the very next request, not after
    the access token expires.
    """

    async def _check(current_user: UserEntity = Depends(get_current_user)) -> UserEntity:
        if not current_user.has_permission(permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission_code}",
            )
        return current_user

    return _check
