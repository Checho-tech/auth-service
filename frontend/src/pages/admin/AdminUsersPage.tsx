import { useEffect, useState } from "react";
import * as adminApi from "../../api/admin";
import { AccessDenied } from "../../components/AccessDenied";
import { Alert } from "../../components/Alert";
import { AppShell } from "../../components/AppShell";
import { Button } from "../../components/Button";
import { Pill } from "../../components/Pill";
import { ApiError, type RoleName, type UserListItem } from "../../types/api";
import "../../styles/table.css";
import "./AdminUsersPage.css";

const ALL_ROLES: RoleName[] = ["admin", "manager", "employee"];

function sameRoles(a: string[], b: string[]): boolean {
  return [...a].sort().join(",") === [...b].sort().join(",");
}

function UserRow({
  user,
  onUpdated,
}: {
  user: UserListItem;
  onUpdated: (updated: UserListItem) => void;
}) {
  const [pendingRoles, setPendingRoles] = useState<RoleName[]>(user.roles as RoleName[]);
  const [saving, setSaving] = useState(false);
  const [deactivating, setDeactivating] = useState(false);
  const [rowError, setRowError] = useState<string | null>(null);

  const dirty = !sameRoles(pendingRoles, user.roles);

  function toggleRole(role: RoleName) {
    setPendingRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role],
    );
  }

  async function handleSave() {
    setSaving(true);
    setRowError(null);
    try {
      const updated = await adminApi.assignRoles(user.id, pendingRoles);
      onUpdated(updated);
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : "Could not update roles.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate() {
    if (!window.confirm(`Deactivate ${user.email}? They will no longer be able to sign in.`)) {
      return;
    }
    setDeactivating(true);
    setRowError(null);
    try {
      await adminApi.deactivateUser(user.id);
      onUpdated({ ...user, is_active: false });
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : "Could not deactivate user.");
    } finally {
      setDeactivating(false);
    }
  }

  return (
    <tr>
      <td>
        <div>{user.email}</div>
        {user.full_name ? <div className="table-cell-muted">{user.full_name}</div> : null}
      </td>
      <td>
        <div className="detail-pills">
          <Pill tone={user.is_active ? "success" : "danger"}>
            {user.is_active ? "Active" : "Deactivated"}
          </Pill>
          <Pill tone={user.is_verified ? "success" : "warning"}>
            {user.is_verified ? "Verified" : "Unverified"}
          </Pill>
        </div>
      </td>
      <td>
        <div className="role-toggle-group">
          {ALL_ROLES.map((role) => (
            <button
              key={role}
              type="button"
              className={["role-toggle", pendingRoles.includes(role) ? "role-toggle-active" : ""]
                .filter(Boolean)
                .join(" ")}
              onClick={() => toggleRole(role)}
              disabled={saving}
            >
              {role}
            </button>
          ))}
        </div>
        {rowError ? <div className="field-error admin-row-error">{rowError}</div> : null}
      </td>
      <td>
        <div className="row-actions">
          {dirty ? (
            <Button variant="secondary" onClick={() => void handleSave()} loading={saving}>
              Save roles
            </Button>
          ) : null}
          <Button
            variant="danger"
            onClick={() => void handleDeactivate()}
            loading={deactivating}
            disabled={!user.is_active}
          >
            Deactivate
          </Button>
        </div>
      </td>
    </tr>
  );
}

export function AdminUsersPage() {
  const [users, setUsers] = useState<UserListItem[] | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    adminApi
      .listUsers()
      .then(setUsers)
      .catch((err: unknown) => setError(err instanceof ApiError ? err : new ApiError(0, "Failed to load users.")));
  }, []);

  function handleUpdated(updated: UserListItem) {
    setUsers((prev) => (prev ? prev.map((u) => (u.id === updated.id ? updated : u)) : prev));
  }

  return (
    <AppShell title="Users" description="Manage roles and account status for every user.">
      {error?.status === 403 ? <AccessDenied permission="users:read" /> : null}
      {error && error.status !== 403 ? <Alert tone="danger">{error.message}</Alert> : null}
      {!error && !users ? <p className="table-cell-muted">Loading users…</p> : null}
      {!error && users ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Status</th>
                <th>Roles</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={4} className="table-empty">
                    No users yet.
                  </td>
                </tr>
              ) : (
                users.map((user) => <UserRow key={user.id} user={user} onUpdated={handleUpdated} />)
              )}
            </tbody>
          </table>
        </div>
      ) : null}
    </AppShell>
  );
}
