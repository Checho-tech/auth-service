// Mirrors the Pydantic schemas in src/auth_service/interfaces/api/v1/schemas/*.py

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface MessageResponse {
  message: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  roles: string[];
}

export interface UserListItem {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  roles: string[];
}

export interface AuditLogEntry {
  id: string;
  event_type: string;
  user_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export type RoleName = "admin" | "manager" | "employee";

// Every permission code seeded in alembic/versions/..._seed_default_roles_and_permissions.py
export type PermissionCode =
  | "users:read"
  | "users:write"
  | "users:delete"
  | "roles:manage"
  | "audit:read";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}
