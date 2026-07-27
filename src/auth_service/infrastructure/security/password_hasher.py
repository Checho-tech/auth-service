"""Password hashing via bcrypt (through passlib).

bcrypt is deliberately slow (adaptive work factor) so brute-forcing a
stolen hash is expensive — unlike fast hashes (MD5/SHA-256) which are
designed for speed and are a poor fit for password storage.
"""

from passlib.context import CryptContext

from auth_service.domain.exceptions import WeakPasswordError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# NIST 800-63B favors length over forced complexity rules (upper/lower/
# digit/symbol requirements tend to push users toward predictable patterns
# like "Passw0rd!"). We enforce a high minimum length instead.
MIN_PASSWORD_LENGTH = 12

# A tiny, illustrative blocklist — not a substitute for a real breached-
# password API (e.g. HaveIBeenPwned's k-anonymity endpoint), which would be
# the production-grade choice. Kept local/offline for portfolio simplicity.
_COMMON_PASSWORDS = {"password123456", "123456789012", "qwertyuiop123", "letmein123456"}


def validate_password_strength(password: str, email: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
    if password.lower() in _COMMON_PASSWORDS:
        raise WeakPasswordError("This password is too common. Please choose a different one.")
    if password.lower() == email.lower():
        raise WeakPasswordError("Password must not be the same as your email address.")


def hash_password(plain_password: str) -> str:
    # passlib has no type stubs, so its return type is untyped/Any at
    # mypy's eyes — the explicit str()/bool() calls below make the real,
    # already-guaranteed return type visible to the type checker.
    return str(_pwd_context.hash(plain_password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bool(_pwd_context.verify(plain_password, hashed_password))
