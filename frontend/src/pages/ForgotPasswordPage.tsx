import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import * as authApi from "../api/auth";
import { Alert } from "../components/Alert";
import { AuthLayout } from "../components/AuthLayout";
import { Button } from "../components/Button";
import { TextField } from "../components/TextField";
import { ApiError } from "../types/api";
import "../styles/forms.css";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await authApi.forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (sent) {
    return (
      <AuthLayout
        title="Check the logs"
        subtitle="If that email is registered, a reset token was issued."
        footer={
          <>
            <Link to="/reset-password">Continue to reset password</Link>
          </>
        }
      >
        <Alert tone="neutral">
          Same response either way — this prevents confirming whether an email is registered. Find
          the token with:
          <br />
          <code className="mono">docker compose logs app | grep mock_email_sent</code>
        </Alert>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Forgot your password?"
      subtitle="Enter your email and we'll issue a reset token."
      footer={
        <>
          Remembered it? <Link to="/login">Sign in</Link>
        </>
      }
    >
      <form className="form-stack" onSubmit={handleSubmit}>
        {error ? <Alert tone="danger">{error}</Alert> : null}
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <div className="form-actions form-actions-stretch">
          <Button type="submit" loading={submitting}>
            Send reset token
          </Button>
        </div>
      </form>
    </AuthLayout>
  );
}
