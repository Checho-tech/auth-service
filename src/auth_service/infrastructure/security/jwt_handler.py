"""JWT encode/decode using PyJWT.

Two token types share this module but are never interchangeable:
  - "access"  -> short-lived, sent on every request, never stored server-side.
  - "refresh" -> long-lived, stored (hashed) in `refresh_tokens` so it can be revoked.

We ALWAYS pass `algorithms=[settings.jwt_algorithm]` explicitly to `jwt.decode`.
Omitting this lets an attacker submit a token whose header claims a different
(weaker, or "none") algorithm, and some libraries will trust that instead of
what the server expects — the "algorithm confusion" vulnerability class.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import jwt

from auth_service.domain.exceptions import InvalidTokenError
from auth_service.infrastructure.config import get_settings

TokenType = Literal["access", "refresh", "email_verification"]


def _create_token(
    user_id: UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID, role_names: tuple[str, ...]) -> str:
    settings = get_settings()
    return _create_token(
        user_id,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"roles": list(role_names)},
    )


def create_refresh_token(user_id: UUID) -> str:
    settings = get_settings()
    return _create_token(user_id, "refresh", timedelta(days=settings.refresh_token_expire_days))


def create_email_verification_token(user_id: UUID) -> str:
    # Stateless on purpose: verifying an email is idempotent (doing it twice
    # is harmless), so there's no need for the DB-tracked revocation that
    # refresh/reset tokens require. The signature alone prevents tampering.
    return _create_token(user_id, "email_verification", timedelta(hours=24))


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise InvalidTokenError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("Token is invalid.") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected a '{expected_type}' token.")

    return payload
