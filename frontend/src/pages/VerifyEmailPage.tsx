import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import * as authApi from "../api/auth";
import { Alert } from "../components/Alert";
import { AuthLayout } from "../components/AuthLayout";
import { Button } from "../components/Button";
import { TextField } from "../components/TextField";
import { ApiError } from "../types/api";
import "../styles/forms.css";

export function VerifyEmailPage() {
  const navigate = useNavigate();
  const location = useLocation() as { state?: { email?: string } };
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState(searchParams.get("token") ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verified, setVerified] = useState(false);

  const email = location.state?.email;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await authApi.verifyEmail(token.trim());
      setVerified(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (verified) {
    return (
      <AuthLayout title="Email verified" subtitle="Your account is ready to use.">
        <Alert tone="success">Your email address has been confirmed.</Alert>
        <div className="form-actions form-actions-stretch">
          <Button onClick={() => navigate("/login")}>Continue to sign in</Button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Verify your email"
      subtitle={
        email
          ? `We "sent" a verification link to ${email}.`
          : "Paste the verification token to activate your account."
      }
      footer={
        <>
          Already verified? <Link to="/login">Sign in</Link>
        </>
      }
    >
      <Alert tone="neutral">
        This demo doesn't send real email — it logs the message instead. Find the token with:
        <br />
        <code className="mono">docker compose logs app | grep mock_email_sent</code>
      </Alert>
      <form className="form-stack" onSubmit={handleSubmit}>
        {error ? <Alert tone="danger">{error}</Alert> : null}
        <TextField
          label="Verification token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          required
          className="mono"
        />
        <div className="form-actions form-actions-stretch">
          <Button type="submit" loading={submitting}>
            Verify email
          </Button>
        </div>
      </form>
    </AuthLayout>
  );
}
