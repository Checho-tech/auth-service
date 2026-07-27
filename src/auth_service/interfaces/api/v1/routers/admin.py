"""Admin/user-management endpoints — each one guarded by a specific permission."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from auth_service.application.services.user_management_service import UserManagementService
from auth_service.domain.entities import UserEntity
from auth_service.interfaces.api.dependencies import get_user_management_service, require_permission
from auth_service.interfaces.api.v1.schemas.admin_schemas import (
    AssignRolesRequest,
    AuditLogEntryResponse,
    UserListItemResponse,
)
from auth_service.interfaces.api.v1.schemas.auth_schemas import MessageResponse

router = APIRouter(prefix="/api/v1", tags=["admin"])


def _to_user_list_item(user: UserEntity) -> UserListItemResponse:
    return UserListItemResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        roles=list(user.role_names),
    )


@router.get("/users", response_model=list[UserListItemResponse])
async def list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    _: UserEntity = Depends(require_permission("users:read")),
    service: UserManagementService = Depends(get_user_management_service),
) -> list[UserListItemResponse]:
    users = await service.list_users(offset=offset, limit=limit)
    return [_to_user_list_item(u) for u in users]


@router.patch("/users/{user_id}/roles", response_model=UserListItemResponse)
async def assign_roles(
    user_id: UUID,
    body: AssignRolesRequest,
    current_user: UserEntity = Depends(require_permission("roles:manage")),
    service: UserManagementService = Depends(get_user_management_service),
) -> UserListItemResponse:
    updated = await service.assign_roles(current_user.id, user_id, tuple(body.roles))
    return _to_user_list_item(updated)


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def deactivate_user(
    user_id: UUID,
    current_user: UserEntity = Depends(require_permission("users:delete")),
    service: UserManagementService = Depends(get_user_management_service),
) -> MessageResponse:
    await service.deactivate_user(current_user.id, user_id)
    return MessageResponse(message="User deactivated successfully.")


@router.get("/audit-logs", response_model=list[AuditLogEntryResponse])
async def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    _: UserEntity = Depends(require_permission("audit:read")),
    service: UserManagementService = Depends(get_user_management_service),
) -> list[AuditLogEntryResponse]:
    entries = await service.list_audit_logs(limit=limit)
    return [
        AuditLogEntryResponse(
            id=e.id,
            event_type=e.event_type,
            user_id=e.user_id,
            ip_address=e.ip_address,
            user_agent=e.user_agent,
            metadata=e.metadata,
            created_at=e.created_at,
        )
        for e in entries
    ]
