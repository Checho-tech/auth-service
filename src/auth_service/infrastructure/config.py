"""Application settings, loaded from environment variables (.env in local dev).

Using pydantic-settings instead of raw `os.getenv()` gives us two things
`os.getenv` cannot: type coercion (e.g. "15" -> int) and fail-fast validation.
If a required variable is missing, the app refuses to start instead of running
with a silent `None` that would surface as a confusing bug later.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Authentication Service"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    database_url: str

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    max_failed_login_attempts: int = 5
    account_lock_duration_minutes: int = 15

    rate_limit_login: str = "5/minute"

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from_email: str = "noreply@auth-service.local"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — parsed from env once per process."""
    return Settings()  # type: ignore[call-arg]
