"""RBAC enforcement at the HTTP layer, against a real database."""

PASSWORD = "IntegrationTestPass2026!"


def _extract_token(sent_emails: list[dict], to: str) -> str:
    email = next(e for e in reversed(sent_emails) if e["to"] == to)
    return email["body"].split(": ")[1]


async def _register_login_verified_user(client, mock_sent_emails, email: str) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Integration User"},
    )
    token = _extract_token(mock_sent_emails, email)
    await client.post("/api/v1/auth/verify-email", json={"token": token})
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return response.json()


class TestPermissionEnforcement:
    async def test_employee_without_audit_read_permission_gets_403(self, client, mock_sent_emails):
        pair = await _register_login_verified_user(client, mock_sent_emails, "rbac-employee@example.com")

        response = await client.get(
            "/api/v1/audit-logs", headers={"Authorization": f"Bearer {pair['access_token']}"}
        )

        assert response.status_code == 403
        assert "audit:read" in response.json()["detail"]

    async def test_role_change_via_api_takes_effect_without_new_login(
        self, client, mock_sent_emails, promote_to_admin
    ):
        # Bootstrap the very first admin out-of-band (direct SQL — see the
        # `promote_to_admin` fixture docstring), then do everything else
        # through the real API, exactly like Fase 4's manual walkthrough.
        await _register_login_verified_user(client, mock_sent_emails, "bootstrap-admin@example.com")
        await promote_to_admin("bootstrap-admin@example.com")
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "bootstrap-admin@example.com", "password": PASSWORD},
        )
        admin_token = admin_login.json()["access_token"]

        target_pair = await _register_login_verified_user(client, mock_sent_emails, "rbac-target@example.com")
        old_access_token = target_pair["access_token"]
        me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {old_access_token}"})
        target_id = me.json()["id"]

        # Old token, issued before the promotion below, has no audit:read yet.
        before = await client.get(
            "/api/v1/audit-logs", headers={"Authorization": f"Bearer {old_access_token}"}
        )
        assert before.status_code == 403

        assign_response = await client.patch(
            f"/api/v1/users/{target_id}/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"roles": ["admin"]},
        )
        assert assign_response.status_code == 200

        # Same OLD token, never refreshed — proves the permission check is
        # re-evaluated from the DB on every request, not cached in the JWT.
        after = await client.get(
            "/api/v1/audit-logs", headers={"Authorization": f"Bearer {old_access_token}"}
        )
        assert after.status_code == 200


class TestAccountDeactivation:
    async def test_deactivated_user_cannot_log_in_again(self, client, mock_sent_emails, promote_to_admin):
        await _register_login_verified_user(client, mock_sent_emails, "deactivate-admin@example.com")
        await promote_to_admin("deactivate-admin@example.com")
        # Re-login to get a token that reflects the just-granted admin role
        relogin = await client.post(
            "/api/v1/auth/login",
            json={"email": "deactivate-admin@example.com", "password": PASSWORD},
        )
        admin_token = relogin.json()["access_token"]

        victim_pair = await _register_login_verified_user(client, mock_sent_emails, "deactivate-victim@example.com")
        me = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {victim_pair['access_token']}"}
        )
        victim_id = me.json()["id"]

        deactivate_response = await client.delete(
            f"/api/v1/users/{victim_id}", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert deactivate_response.status_code == 200

        login_attempt = await client.post(
            "/api/v1/auth/login",
            json={"email": "deactivate-victim@example.com", "password": PASSWORD},
        )

        assert login_attempt.status_code == 403
        assert "deactivated" in login_attempt.json()["detail"].lower()
