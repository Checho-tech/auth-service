import { useState, type FormEvent } from "react";
import * as authApi from "../api/auth";
import { Alert } from "../components/Alert";
import { AppShell } from "../components/AppShell";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Pill } from "../components/Pill";
import { TextField } from "../components/TextField";
import { useAuth } from "../context/useAuth";
import { ApiError } from "../types/api";
import "../styles/forms.css";
import "./DashboardPage.css";

export function DashboardPage() {
  const { user } = useAuth();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleChangePassword(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);
    try {
      const response = await authApi.changePassword(oldPassword, newPassword);
      setSuccess(response.message);
      setOldPassword("");
      setNewPassword("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!user) return null;

  return (
    <AppShell title="Profile" description="Your account details and session security.">
      <Card>
        <dl className="detail-grid">
          <div className="detail-row">
            <dt>Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div className="detail-row">
            <dt>Full name</dt>
            <dd>{user.full_name || <span className="detail-empty">Not set</span>}</dd>
          </div>
          <div className="detail-row">
            <dt>User ID</dt>
            <dd className="mono detail-id">{user.id}</dd>
          </div>
          <div className="detail-row">
            <dt>Status</dt>
            <dd className="detail-pills">
              <Pill tone={user.is_active ? "success" : "danger"}>
                {user.is_active ? "Active" : "Deactivated"}
              </Pill>
              <Pill tone={user.is_verified ? "success" : "warning"}>
                {user.is_verified ? "Verified" : "Unverified"}
              </Pill>
            </dd>
          </div>
          <div className="detail-row">
            <dt>Roles</dt>
            <dd className="detail-pills">
              {user.roles.map((role) => (
                <Pill key={role} tone="accent">
                  {role}
                </Pill>
              ))}
            </dd>
          </div>
        </dl>
      </Card>

      <Card>
        <h2 className="dashboard-section-title">Change password</h2>
        <p className="dashboard-section-description">
          Changing your password signs you out of every other active session.
        </p>
        <form className="form-stack dashboard-password-form" onSubmit={handleChangePassword}>
          {error ? <Alert tone="danger">{error}</Alert> : null}
          {success ? <Alert tone="success">{success}</Alert> : null}
          <TextField
            label="Current password"
            type="password"
            autoComplete="current-password"
            required
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
          />
          <TextField
            label="New password"
            type="password"
            autoComplete="new-password"
            required
            minLength={12}
            hint="At least 12 characters."
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <div className="form-actions">
            <Button type="submit" loading={submitting}>
              Update password
            </Button>
          </div>
        </form>
      </Card>
    </AppShell>
  );
}
