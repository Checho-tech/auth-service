"""Pydantic schemas for admin/user-management endpoints."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

# Mirrors the roles seeded in the "seed default roles and permissions"
# migration. Using Literal here means an invalid role name is rejected by
# Pydantic at the API boundary (422) before it ever reaches the service layer.
RoleName = Literal["admin", "manager", "employee"]


class UserListItemResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    roles: list[str]


class AssignRolesRequest(BaseModel):
    roles: list[RoleName]


class AuditLogEntryResponse(BaseModel):
    id: UUID
    event_type: str
    user_id: UUID | None
    ip_address: str | None
    user_agent: str | None
    metadata: dict[str, object] | None
    created_at: datetime
