"""AuthService: orchestrates registration, login, token refresh, logout,
and password management.

This class depends only on interfaces (application/interfaces), never on
SQLAlchemy or FastAPI directly — that's what makes it unit-testable without
a real database (Fase 5 will mock every one of these dependencies).
"""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from auth_service.application.interfaces import (
    IAuditLogRepository,
    IEmailSender,
    IPasswordResetRepository,
    IRefreshTokenRepository,
    IUserRepository,
)
from auth_service.domain.entities import UserEntity
from auth_service.domain.exceptions import (
    AccountDeactivatedError,
    AccountLockedError,
    AccountNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    RefreshTokenReuseDetectedError,
    UserAlreadyExistsError,
)
from auth_service.infrastructure.config import Settings
from auth_service.infrastructure.security.jwt_handler import (
    create_access_token,
    create_email_verification_token,
    create_refresh_token,
    decode_token,
)
from auth_service.infrastructure.security.password_hasher import (
    hash_password,
    validate_password_strength,
    verify_password,
)
from auth_service.infrastructure.security.token_hasher import hash_token


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthService:
    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
        password_reset_repo: IPasswordResetRepository,
        audit_log_repo: IAuditLogRepository,
        email_sender: IEmailSender,
        settings: Settings,
    ) -> None:
        self._users = user_repo
        self._refresh_tokens = refresh_token_repo
        self._password_resets = password_reset_repo
        self._audit = audit_log_repo
        self._email = email_sender
        self._settings = settings

    async def register(self, email: str, password: str, full_name: str | None) -> UserEntity:
        validate_password_strength(password, email)

        if await self._users.get_by_email(email) is not None:
            raise UserAlreadyExistsError(email)

        user = await self._users.create(email, hash_password(password), full_name)

        verification_token = create_email_verification_token(self._settings, user.id)
        await self._email.send(
            to=email,
            subject="Verify your email",
            body=f"Use this token to verify your account: {verification_token}",
        )
        await self._audit.log_event("user_registered", user.id, None, None)
        return user

    async def verify_email(self, token: str) -> None:
        try:
            payload = decode_token(self._settings, token, expected_type="email_verification")
        except InvalidTokenError:
            raise
        user_id = UUID(payload["sub"])
        await self._users.set_verified(user_id, True)
        await self._audit.log_event("email_verified", user_id, None, None)

    async def login(
        self, email: str, password: str, ip_address: str | None, user_agent: str | None
    ) -> TokenPair:
        user = await self._users.get_by_email(email)
        now = datetime.now(UTC)

        if user is None:
            # Same error as a wrong password: don't reveal whether the email exists.
            await self._audit.log_event(
                "login_failed", None, ip_address, user_agent, {"email": email}
            )
            raise InvalidCredentialsError()

        if user.is_locked(now):
            await self._audit.log_event("login_failed_locked", user.id, ip_address, user_agent)
            raise AccountLockedError(user.locked_until.isoformat())  # type: ignore[union-attr]

        if not verify_password(password, user.hashed_password):
            await self._register_failed_attempt(user, ip_address, user_agent)
            raise InvalidCredentialsError()

        # Checked only after a correct password, not before: doing it earlier
        # would let an unauthenticated caller learn "this email belongs to a
        # deactivated account" without ever proving they know the password.
        if not user.is_active:
            await self._audit.log_event("login_failed_deactivated", user.id, ip_address, user_agent)
            raise AccountDeactivatedError()

        if not user.is_verified:
            raise AccountNotVerifiedError()

        await self._users.reset_failed_login(user.id)
        await self._audit.log_event("login_success", user.id, ip_address, user_agent)
        return await self._issue_token_pair(user.id, user.role_names, user_agent)

    async def _register_failed_attempt(
        self, user: UserEntity, ip_address: str | None, user_agent: str | None
    ) -> None:
        attempts = user.failed_login_attempts + 1
        locked_until = None
        event = "login_failed"
        if attempts >= self._settings.max_failed_login_attempts:
            locked_until = datetime.now(UTC) + timedelta(
                minutes=self._settings.account_lock_duration_minutes
            )
            event = "account_locked"
        await self._users.register_failed_login(user.id, attempts, locked_until)
        await self._audit.log_event(
            event, user.id, ip_address, user_agent, {"attempts": attempts}
        )

    async def _issue_token_pair(
        self, user_id: UUID, role_names: tuple[str, ...], user_agent: str | None
    ) -> TokenPair:
        access_token = create_access_token(self._settings, user_id, role_names)
        refresh_token = create_refresh_token(self._settings, user_id)
        payload = decode_token(self._settings, refresh_token, expected_type="refresh")
        await self._refresh_tokens.create(
            user_id=user_id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            user_agent=user_agent,
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, raw_refresh_token: str, user_agent: str | None) -> TokenPair:
        # Return value unused on purpose: decoding still validates the
        # signature and expiry as a side effect, raising InvalidTokenError
        # before we ever touch the DB for a forged or expired token.
        decode_token(self._settings, raw_refresh_token, expected_type="refresh")
        token_hash = hash_token(raw_refresh_token)
        stored = await self._refresh_tokens.get_by_hash(token_hash)

        if stored is None:
            raise InvalidTokenError("Refresh token not recognized.")

        if stored.revoked_at is not None:
            # Rotation invariant: a legitimate client always gets a fresh
            # token and stops using the old one. Seeing the old one again
            # means someone else (an attacker) captured it first.
            await self._refresh_tokens.revoke_all_for_user(stored.user_id)
            await self._audit.log_event(
                "refresh_token_reuse_detected", stored.user_id, None, user_agent
            )
            raise RefreshTokenReuseDetectedError()

        if stored.expires_at < datetime.now(UTC):
            raise InvalidTokenError("Refresh token has expired.")

        user = await self._users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise InvalidTokenError("User no longer exists or is inactive.")

        await self._refresh_tokens.revoke(token_hash)
        await self._audit.log_event("token_refreshed", user.id, None, user_agent)
        return await self._issue_token_pair(user.id, user.role_names, user_agent)

    async def logout(self, raw_refresh_token: str) -> None:
        await self._refresh_tokens.revoke(hash_token(raw_refresh_token))

    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> None:
        user = await self._users.get_by_id(user_id)
        if user is None or not verify_password(old_password, user.hashed_password):
            raise InvalidCredentialsError()

        validate_password_strength(new_password, user.email)
        await self._users.update_password(user_id, hash_password(new_password))
        # Changing the password invalidates every existing session — if an
        # attacker had a stolen session, this locks them out immediately.
        await self._refresh_tokens.revoke_all_for_user(user_id)
        await self._audit.log_event("password_changed", user_id, None, None)

    async def request_password_reset(self, email: str) -> None:
        user = await self._users.get_by_email(email)
        if user is None:
            # Deliberately silent: responding differently for unknown emails
            # would let an attacker enumerate registered accounts.
            return

        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        await self._password_resets.create(user.id, hash_token(raw_token), expires_at)
        await self._email.send(
            to=email,
            subject="Reset your password",
            body=f"Use this token to reset your password: {raw_token}",
        )
        await self._audit.log_event("password_reset_requested", user.id, None, None)

    async def reset_password(self, raw_token: str, new_password: str) -> None:
        token_hash = hash_token(raw_token)
        stored = await self._password_resets.get_by_hash(token_hash)

        if stored is None or stored.used_at is not None or stored.expires_at < datetime.now(UTC):
            raise InvalidTokenError("Reset token is invalid, expired, or already used.")

        user = await self._users.get_by_id(stored.user_id)
        if user is None:
            raise InvalidTokenError("User no longer exists.")

        validate_password_strength(new_password, user.email)
        await self._users.update_password(stored.user_id, hash_password(new_password))
        await self._password_resets.mark_used(token_hash)
        await self._refresh_tokens.revoke_all_for_user(stored.user_id)
        # Successfully resetting the password proves ownership of the
        # mailbox — an account-lockout from earlier failed login attempts
        # should not persist past that, or the user would be stuck locked
        # out even after proving who they are.
        await self._users.reset_failed_login(stored.user_id)
        await self._audit.log_event("password_reset_completed", stored.user_id, None, None)

    async def get_profile(self, user_id: UUID) -> UserEntity:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError("User no longer exists.")
        return user
