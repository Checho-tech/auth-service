import type { AuditLogEntry, MessageResponse, RoleName, UserListItem } from "../types/api";
import { apiFetch } from "./client";

export function listUsers(): Promise<UserListItem[]> {
  return apiFetch<UserListItem[]>("/api/v1/users?limit=200", { method: "GET" });
}

export function assignRoles(userId: string, roles: RoleName[]): Promise<UserListItem> {
  return apiFetch<UserListItem>(`/api/v1/users/${userId}/roles`, {
    method: "PATCH",
    body: { roles },
  });
}

export function deactivateUser(userId: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>(`/api/v1/users/${userId}`, { method: "DELETE" });
}

export function listAuditLogs(): Promise<AuditLogEntry[]> {
  return apiFetch<AuditLogEntry[]>("/api/v1/audit-logs?limit=200", { method: "GET" });
}
