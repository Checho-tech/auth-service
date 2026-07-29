"""Application settings, loaded from environment variables (.env in local dev).

Using pydantic-settings instead of raw `os.getenv()` gives us two things
`os.getenv` cannot: type coercion (e.g. "15" -> int) and fail-fast validation.
If a required variable is missing, the app refuses to start instead of running
with a silent `None` that would surface as a confusing bug later.
"""

import hashlib
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Authentication Service"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    database_url: str

    # RS256: the private key signs tokens (never leaves this service); the
    # public key verifies them and is safe to hand out freely — that's the
    # whole point of asymmetric signing versus a single shared HS256 secret
    # (see docs/00_NOTAS_PERSONALES_INSTALACIONES.txt for the full rationale,
    # written when Project 2 — a separate service consuming these tokens —
    # made the shared-secret approach a real liability).
    jwt_algorithm: str = "RS256"
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    max_failed_login_attempts: int = 5
    account_lock_duration_minutes: int = 15

    rate_limit_login: str = "5/minute"

    # Comma-separated in .env (e.g. "http://localhost:5173,https://app.example.com");
    # the frontend's dev server and, later, its deployed origin both need to be listed.
    cors_origins: str = "http://localhost:5173"

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from_email: str = "noreply@auth-service.local"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @cached_property
    def jwt_private_key(self) -> str:
        return Path(self.jwt_private_key_path).read_text()

    @cached_property
    def jwt_public_key(self) -> str:
        return Path(self.jwt_public_key_path).read_text()

    @cached_property
    def jwt_key_id(self) -> str:
        """Stable identifier for the current public key (the JWT header's "kid").

        Derived from the key's own bytes rather than hand-assigned, so it
        changes automatically the moment the key pair is rotated — a
        consumer's PyJWKClient matches this against the token's header to
        pick the right key out of the JWKS response.
        """
        return hashlib.sha256(self.jwt_public_key.encode()).hexdigest()[:16]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — parsed from env once per process."""
    return Settings()  # type: ignore[call-arg]
