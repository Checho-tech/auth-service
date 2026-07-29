"""Integration test fixtures: a real, disposable Postgres container.

Deliberately plain `subprocess` + the Docker CLI, rather than a library like
testcontainers-python: it's the exact same container lifecycle (start,
poll pg_isready, run migrations, tear down) already proven to work in this
environment throughout Fases 2-4, with no extra dependency to manage.

Runs on port 5433 (not 5432) and a separate database name, so it never
collides with whatever Postgres a developer might already have running
locally for manual testing.
"""

import os
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTAINER_NAME = "auth_service_test_pg"
TEST_DB_PORT = 5433
TEST_DATABASE_URL = f"postgresql+asyncpg://auth_user:changeme@localhost:{TEST_DB_PORT}/auth_service_test_db"

# Must happen at *import* time (module level), before any test module pulls
# in `auth_service.main` (which reads settings — cached — on import). Pytest
# imports every conftest.py during collection, before running any test, so
# this always wins the race regardless of test execution order.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
# The production rate limit (5/minute on login) is deliberately strict —
# but the test suite legitimately logs in far more than 5 times per minute
# across different tests, all appearing to slowapi as the same client "IP".
# Loosening it here is a test-environment concern, not a security relaxation.
os.environ["RATE_LIMIT_LOGIN"] = "1000/minute"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from tests.rsa_test_keys import generate_test_keypair  # noqa: E402

# Required by Settings with no default — set here so the integration suite
# never depends on a developer's local .env existing. A CI runner (or a
# fresh clone) has neither, and previously this only "worked" locally by
# accident because a real .env happened to be present.
_private_key_path, _public_key_path = generate_test_keypair()
os.environ.setdefault("JWT_PRIVATE_KEY_PATH", _private_key_path)
os.environ.setdefault("JWT_PUBLIC_KEY_PATH", _public_key_path)


@pytest.fixture(scope="session", autouse=True)
def postgres_test_container():
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
    subprocess.run(
        [
            "docker", "run", "-d", "--name", CONTAINER_NAME,
            "-e", "POSTGRES_USER=auth_user",
            "-e", "POSTGRES_PASSWORD=changeme",
            "-e", "POSTGRES_DB=auth_service_test_db",
            "-p", f"{TEST_DB_PORT}:5432",
            "postgres:16-alpine",
        ],
        check=True,
        capture_output=True,
    )

    for _ in range(30):
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "pg_isready", "-U", "auth_user"],
            capture_output=True,
        )
        if result.returncode == 0:
            break
        time.sleep(1)
    else:
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
        raise RuntimeError("Postgres test container did not become ready in time.")

    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        cwd=str(REPO_ROOT),
        env={**os.environ, "DATABASE_URL": TEST_DATABASE_URL},
    )

    yield

    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)


@pytest_asyncio.fixture
async def client():
    from auth_service.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def promote_to_admin():
    """Directly grants the 'admin' role to a user, bypassing the API.

    Mirrors the manual bootstrap done via `docker exec psql` in Fase 4:
    there is no admin account to begin with, so the very first admin has
    to be created out-of-band. Real deployments would use a management
    script instead of raw SQL (documented as a follow-up in the README).
    """
    import asyncpg

    async def _promote(email: str) -> None:
        conn = await asyncpg.connect(
            user="auth_user", password="changeme", database="auth_service_test_db",
            host="localhost", port=TEST_DB_PORT,
        )
        try:
            await conn.execute(
                """
                INSERT INTO user_roles (user_id, role_id)
                SELECT u.id, r.id FROM users u, roles r
                WHERE u.email = $1 AND r.name = 'admin'
                ON CONFLICT DO NOTHING
                """,
                email,
            )
        finally:
            await conn.close()

    return _promote


@pytest.fixture
def mock_sent_emails(monkeypatch):
    """Capture every "sent" email in-memory instead of only logging it,
    so integration tests can pull out verification/reset tokens directly.
    """
    sent: list[dict] = []

    async def _fake_send(self, to: str, subject: str, body: str) -> None:
        sent.append({"to": to, "subject": subject, "body": body})

    from auth_service.infrastructure.email.console_email_sender import ConsoleEmailSender

    monkeypatch.setattr(ConsoleEmailSender, "send", _fake_send)
    return sent
