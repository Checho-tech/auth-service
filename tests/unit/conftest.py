import pytest

from auth_service.application.services.auth_service import AuthService
from auth_service.application.services.user_management_service import UserManagementService
from auth_service.infrastructure.config import Settings
from tests.rsa_test_keys import generate_test_keypair
from tests.unit.fakes import (
    FakeAuditLogRepository,
    FakeEmailSender,
    FakePasswordResetRepository,
    FakeRefreshTokenRepository,
    FakeUserRepository,
)

_TEST_PRIVATE_KEY_PATH, _TEST_PUBLIC_KEY_PATH = generate_test_keypair()

# Built directly, NOT via get_settings(): unit tests never touch the
# process-wide lru_cache, so they can't leak configuration into (or from)
# the integration test suite, which relies on that same cache being fresh.
TEST_SETTINGS = Settings(
    database_url="postgresql+asyncpg://unused:unused@localhost/unused",
    jwt_private_key_path=_TEST_PRIVATE_KEY_PATH,
    jwt_public_key_path=_TEST_PUBLIC_KEY_PATH,
    max_failed_login_attempts=3,
    account_lock_duration_minutes=15,
)


@pytest.fixture
def user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def refresh_token_repo() -> FakeRefreshTokenRepository:
    return FakeRefreshTokenRepository()


@pytest.fixture
def password_reset_repo() -> FakePasswordResetRepository:
    return FakePasswordResetRepository()


@pytest.fixture
def audit_log_repo() -> FakeAuditLogRepository:
    return FakeAuditLogRepository()


@pytest.fixture
def email_sender() -> FakeEmailSender:
    return FakeEmailSender()


@pytest.fixture
def auth_service(user_repo, refresh_token_repo, password_reset_repo, audit_log_repo, email_sender) -> AuthService:
    return AuthService(
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
        password_reset_repo=password_reset_repo,
        audit_log_repo=audit_log_repo,
        email_sender=email_sender,
        settings=TEST_SETTINGS,
    )


@pytest.fixture
def user_management_service(user_repo, audit_log_repo) -> UserManagementService:
    return UserManagementService(user_repo=user_repo, audit_log_repo=audit_log_repo)
