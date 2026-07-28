import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import * as authApi from "../api/auth";
import { Alert } from "../components/Alert";
import { AuthLayout } from "../components/AuthLayout";
import { Button } from "../components/Button";
import { TextField } from "../components/TextField";
import { ApiError } from "../types/api";
import "../styles/forms.css";

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState(searchParams.get("token") ?? "");
  const [newPassword, setNewPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await authApi.resetPassword(token.trim(), newPassword);
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <AuthLayout title="Password reset" subtitle="You can now sign in with your new password.">
        <Alert tone="success">Your password has been changed successfully.</Alert>
        <div className="form-actions form-actions-stretch">
          <Button onClick={() => navigate("/login")}>Continue to sign in</Button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Set a new password"
      subtitle="Paste the reset token you received and choose a new password."
      footer={
        <>
          <Link to="/login">Back to sign in</Link>
        </>
      }
    >
      <form className="form-stack" onSubmit={handleSubmit}>
        {error ? <Alert tone="danger">{error}</Alert> : null}
        <TextField
          label="Reset token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          required
          className="mono"
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
        <div className="form-actions form-actions-stretch">
          <Button type="submit" loading={submitting}>
            Reset password
          </Button>
        </div>
      </form>
    </AuthLayout>
  );
}
