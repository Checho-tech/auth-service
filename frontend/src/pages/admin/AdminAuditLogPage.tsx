import { useEffect, useState } from "react";
import * as adminApi from "../../api/admin";
import { AccessDenied } from "../../components/AccessDenied";
import { Alert } from "../../components/Alert";
import { AppShell } from "../../components/AppShell";
import { Pill } from "../../components/Pill";
import { ApiError, type AuditLogEntry } from "../../types/api";
import "../../styles/table.css";

type Tone = "neutral" | "accent" | "success" | "warning" | "danger";

const EVENT_TONE: Record<string, Tone> = {
  user_registered: "accent",
  email_verified: "success",
  login_success: "success",
  token_refreshed: "neutral",
  logout: "neutral",
  login_failed: "warning",
  login_failed_locked: "danger",
  login_failed_deactivated: "danger",
  account_locked: "danger",
  refresh_token_reuse_detected: "danger",
  password_changed: "accent",
  password_reset_requested: "neutral",
  password_reset_completed: "accent",
  roles_assigned: "accent",
  user_deactivated: "danger",
};

function eventTone(eventType: string): Tone {
  return EVENT_TONE[eventType] ?? "neutral";
}

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  });
}

export function AdminAuditLogPage() {
  const [entries, setEntries] = useState<AuditLogEntry[] | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    adminApi
      .listAuditLogs()
      .then(setEntries)
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err : new ApiError(0, "Failed to load audit log.")),
      );
  }, []);

  return (
    <AppShell title="Audit log" description="Every security-relevant event, most recent first.">
      {error?.status === 403 ? <AccessDenied permission="audit:read" /> : null}
      {error && error.status !== 403 ? <Alert tone="danger">{error.message}</Alert> : null}
      {!error && !entries ? <p className="table-cell-muted">Loading audit log…</p> : null}
      {!error && entries ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Event</th>
                <th>User</th>
                <th>IP address</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 ? (
                <tr>
                  <td colSpan={4} className="table-empty">
                    No events recorded yet.
                  </td>
                </tr>
              ) : (
                entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>
                      <Pill tone={eventTone(entry.event_type)}>{entry.event_type}</Pill>
                    </td>
                    <td className="mono table-cell-muted">
                      {entry.user_id ? `${entry.user_id.slice(0, 8)}…` : "—"}
                    </td>
                    <td className="mono table-cell-muted">{entry.ip_address ?? "—"}</td>
                    <td className="mono">{formatTimestamp(entry.created_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : null}
    </AppShell>
  );
}
