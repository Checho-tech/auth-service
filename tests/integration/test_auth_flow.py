"""Full HTTP-level auth flow against a real Postgres instance.

This is the automated version of the manual curl walkthroughs done in
Fases 3 and 4 — same flow, now regression-proof.
"""

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


class TestRegistrationAndLogin:
    async def test_register_verify_login_flow(self, client, mock_sent_emails):
        pair = await _register_login_verified_user(client, mock_sent_emails, "flow@example.com")

        assert "access_token" in pair
        assert "refresh_token" in pair

    async def test_duplicate_registration_returns_409(self, client, mock_sent_emails):
        await _register_login_verified_user(client, mock_sent_emails, "dup-int@example.com")

        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "dup-int@example.com", "password": PASSWORD, "full_name": None},
        )

        assert response.status_code == 409

    async def test_weak_password_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "weak-int@example.com", "password": "short", "full_name": None},
        )

        assert response.status_code == 422

    async def test_login_without_verification_returns_403(self, client, mock_sent_emails):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "unverified-int@example.com", "password": PASSWORD, "full_name": None},
        )

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unverified-int@example.com", "password": PASSWORD},
        )

        assert response.status_code == 403


class TestProtectedProfile:
    async def test_get_me_without_token_returns_401(self, client):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_get_me_with_valid_token_returns_profile(self, client, mock_sent_emails):
        pair = await _register_login_verified_user(client, mock_sent_emails, "profile@example.com")

        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {pair['access_token']}"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == "profile@example.com"


class TestRefreshTokenRotation:
    async def test_refresh_rotates_and_old_token_reuse_is_rejected(self, client, mock_sent_emails):
        pair = await _register_login_verified_user(client, mock_sent_emails, "refresh-int@example.com")

        refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
        assert refreshed.status_code == 200

        reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
        assert reused.status_code == 401
