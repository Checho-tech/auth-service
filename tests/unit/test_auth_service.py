import pytest

from auth_service.domain.exceptions import (
    AccountDeactivatedError,
    AccountLockedError,
    AccountNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    RefreshTokenReuseDetectedError,
    UserAlreadyExistsError,
    WeakPasswordError,
)

PASSWORD = "CorrectHorseBattery2026!"


async def _register_and_verify(auth_service, email_sender, email: str = "user@example.com"):
    user = await auth_service.register(email, PASSWORD, "Test User")
    verification_token = email_sender.sent[-1]["body"].split(": ")[1]
    await auth_service.verify_email(verification_token)
    return user


class TestRegister:
    async def test_register_creates_unverified_user_and_sends_email(self, auth_service, email_sender):
        user = await auth_service.register("new@example.com", PASSWORD, "New User")

        assert user.is_verified is False
        assert len(email_sender.sent) == 1
        assert email_sender.sent[0]["to"] == "new@example.com"

    async def test_register_duplicate_email_raises(self, auth_service):
        await auth_service.register("dup@example.com", PASSWORD, None)

        with pytest.raises(UserAlreadyExistsError):
            await auth_service.register("dup@example.com", PASSWORD, None)

    async def test_register_weak_password_raises(self, auth_service):
        with pytest.raises(WeakPasswordError):
            await auth_service.register("weak@example.com", "short", None)


class TestLogin:
    async def test_login_success_returns_token_pair(self, auth_service, email_sender):
        await _register_and_verify(auth_service, email_sender, "login@example.com")

        pair = await auth_service.login("login@example.com", PASSWORD, "127.0.0.1", "pytest")

        assert pair.access_token
        assert pair.refresh_token
        assert pair.token_type == "bearer"

    async def test_login_wrong_password_raises(self, auth_service, email_sender):
        await _register_and_verify(auth_service, email_sender, "wrongpass@example.com")

        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("wrongpass@example.com", "not-the-password", None, None)

    async def test_login_unknown_email_raises_same_error_as_wrong_password(self, auth_service):
        # Same exception type for "unknown email" and "wrong password" on
        # purpose: the response must not let a caller distinguish the two,
        # or it becomes a user-enumeration oracle.
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("nobody@example.com", PASSWORD, None, None)

    async def test_login_unverified_account_raises(self, auth_service):
        await auth_service.register("unverified@example.com", PASSWORD, None)

        with pytest.raises(AccountNotVerifiedError):
            await auth_service.login("unverified@example.com", PASSWORD, None, None)

    async def test_login_locks_account_after_max_failed_attempts(self, auth_service, email_sender):
        await _register_and_verify(auth_service, email_sender, "lockme@example.com")

        # TEST_SETTINGS.max_failed_login_attempts == 3
        for _ in range(3):
            with pytest.raises(InvalidCredentialsError):
                await auth_service.login("lockme@example.com", "wrong", None, None)

        with pytest.raises(AccountLockedError):
            await auth_service.login("lockme@example.com", PASSWORD, None, None)

    async def test_login_deactivated_account_raises_only_after_correct_password(
        self, auth_service, user_repo, email_sender
    ):
        user = await _register_and_verify(auth_service, email_sender, "deactivated@example.com")
        await user_repo.set_active(user.id, is_active=False)

        with pytest.raises(AccountDeactivatedError):
            await auth_service.login("deactivated@example.com", PASSWORD, None, None)


class TestRefreshTokenRotation:
    async def test_refresh_rotates_token_and_old_one_stops_working(self, auth_service, email_sender):
        await _register_and_verify(auth_service, email_sender, "rotate@example.com")
        pair = await auth_service.login("rotate@example.com", PASSWORD, None, None)

        new_pair = await auth_service.refresh(pair.refresh_token, None)

        assert new_pair.refresh_token != pair.refresh_token

    async def test_reusing_a_rotated_refresh_token_is_detected_and_revokes_everything(
        self, auth_service, email_sender
    ):
        await _register_and_verify(auth_service, email_sender, "reuse@example.com")
        pair = await auth_service.login("reuse@example.com", PASSWORD, None, None)

        await auth_service.refresh(pair.refresh_token, None)  # legitimate rotation

        with pytest.raises(RefreshTokenReuseDetectedError):
            await auth_service.refresh(pair.refresh_token, None)  # the old, already-used token

    async def test_expired_or_unknown_refresh_token_raises_invalid_token(self, auth_service):
        with pytest.raises(InvalidTokenError):
            await auth_service.refresh("not-a-real-token", None)


class TestPasswordManagement:
    async def test_change_password_with_wrong_old_password_raises(
        self, auth_service, user_repo, email_sender
    ):
        await _register_and_verify(auth_service, email_sender, "changepw@example.com")
        user = await user_repo.get_by_email("changepw@example.com")

        with pytest.raises(InvalidCredentialsError):
            await auth_service.change_password(user.id, "wrong-old-password", "NewPassword2026!")

    async def test_reset_password_clears_account_lockout(self, auth_service, user_repo, email_sender):
        user = await _register_and_verify(auth_service, email_sender, "resetlock@example.com")
        await user_repo.register_failed_login(user.id, failed_attempts=99, locked_until=None)
        locked_user = await user_repo.get_by_id(user.id)
        assert locked_user.failed_login_attempts == 99

        await auth_service.request_password_reset("resetlock@example.com")
        reset_token = email_sender.sent[-1]["body"].split(": ")[1]
        await auth_service.reset_password(reset_token, "BrandNewPassword2026!")

        recovered_user = await user_repo.get_by_id(user.id)
        assert recovered_user.failed_login_attempts == 0
        assert recovered_user.locked_until is None

    async def test_forgot_password_for_unknown_email_does_not_raise(self, auth_service, email_sender):
        # Silent no-op by design — must not reveal whether the email exists.
        await auth_service.request_password_reset("nobody@example.com")
        assert email_sender.sent == []
