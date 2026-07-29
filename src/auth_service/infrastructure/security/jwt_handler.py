"""JWT encode/decode using PyJWT, signed with RS256 (asymmetric keys).

Two token types share this module but are never interchangeable:
  - "access"  -> short-lived, sent on every request, never stored server-side.
  - "refresh" -> long-lived, stored (hashed) in `refresh_tokens` so it can be revoked.

Tokens are signed with the PRIVATE key and verified with the PUBLIC key —
deliberately not the same secret for both directions. This service is meant
to be consumed by other, separately-deployed microservices (Project 2:
Inventory Service); with a single shared HS256 secret, every consumer would
need a copy of the exact same string, and any one of them leaking it would
let an attacker forge tokens. With RS256, the public key (exposed at
GET /.well-known/jwks.json) can be handed to any number of consumers freely
— it can only verify, never sign.

Every function takes `settings` as an explicit parameter rather than calling
the global `get_settings()` itself. That's what makes AuthService's unit
tests (Fase 5) work with a hand-built `Settings` instance instead of a real
`.env` file — the first version of this module called `get_settings()`
internally, which happened to work locally only because a real `.env`
physically existed on disk, and failed the moment CI ran without one.

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
from auth_service.infrastructure.config import Settings

TokenType = Literal["access", "refresh", "email_verification"]


def _create_token(
    settings: Settings,
    user_id: UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
        **(extra_claims or {}),
    }
    headers = {"kid": settings.jwt_key_id}
    return jwt.encode(
        payload, settings.jwt_private_key, algorithm=settings.jwt_algorithm, headers=headers
    )


def create_access_token(settings: Settings, user_id: UUID, role_names: tuple[str, ...]) -> str:
    return _create_token(
        settings,
        user_id,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"roles": list(role_names)},
    )


def create_refresh_token(settings: Settings, user_id: UUID) -> str:
    return _create_token(
        settings, user_id, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )


def create_email_verification_token(settings: Settings, user_id: UUID) -> str:
    # Stateless on purpose: verifying an email is idempotent (doing it twice
    # is harmless), so there's no need for the DB-tracked revocation that
    # refresh/reset tokens require. The signature alone prevents tampering.
    return _create_token(settings, user_id, "email_verification", timedelta(hours=24))


def decode_token(settings: Settings, token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_public_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise InvalidTokenError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("Token is invalid.") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected a '{expected_type}' token.")

    return payload
