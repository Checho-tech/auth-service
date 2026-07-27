"""seed default roles and permissions

Revision ID: d9922a8a7497
Revises: 2673e33a035a
Create Date: 2026-07-27 08:58:34.624182

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'd9922a8a7497'
down_revision: Union[str, Sequence[str], None] = '2673e33a035a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Lightweight table handles for data-only inserts (do NOT import the ORM
# models here — migrations must stay independent of application code so
# they keep working even after the models evolve or are deleted).
roles_table = sa.table("roles", sa.column("id", UUID), sa.column("name", sa.String), sa.column("description", sa.String))
permissions_table = sa.table(
    "permissions", sa.column("id", UUID), sa.column("code", sa.String), sa.column("description", sa.String)
)
role_permissions_table = sa.table(
    "role_permissions", sa.column("role_id", UUID), sa.column("permission_id", UUID)
)

ROLES = {
    "admin": "Full access to every resource, including role/permission management.",
    "manager": "Can manage users and read audit logs, but cannot change roles/permissions.",
    "employee": "Can read and update only their own profile.",
}

PERMISSIONS = {
    "users:read": "View user profiles.",
    "users:write": "Create or update user profiles.",
    "users:delete": "Deactivate/delete user accounts.",
    "roles:manage": "Assign roles and edit role-permission mappings.",
    "audit:read": "Read audit log entries.",
}

ROLE_PERMISSION_MAP = {
    "admin": list(PERMISSIONS.keys()),
    "manager": ["users:read", "users:write", "audit:read"],
    "employee": ["users:read"],
}


def upgrade() -> None:
    role_ids = {name: uuid.uuid4() for name in ROLES}
    permission_ids = {code: uuid.uuid4() for code in PERMISSIONS}

    op.bulk_insert(
        roles_table,
        [{"id": role_ids[name], "name": name, "description": desc} for name, desc in ROLES.items()],
    )
    op.bulk_insert(
        permissions_table,
        [{"id": permission_ids[code], "code": code, "description": desc} for code, desc in PERMISSIONS.items()],
    )
    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": role_ids[role_name], "permission_id": permission_ids[perm_code]}
            for role_name, perm_codes in ROLE_PERMISSION_MAP.items()
            for perm_code in perm_codes
        ],
    )


def downgrade() -> None:
    op.execute(role_permissions_table.delete())
    op.execute(permissions_table.delete())
    op.execute(roles_table.delete())
