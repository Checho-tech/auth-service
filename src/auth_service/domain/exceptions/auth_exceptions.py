"""Domain-level exceptions for authentication.

These carry no dependency on FastAPI or SQLAlchemy — the interfaces layer
(routers) is responsible for translating each one into the right HTTP
status code, so the service layer stays framework-agnostic.
"""


class DomainError(Exception):
    """Base class for every domain exception in this service."""


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"A user with email '{email}' already exists.")


class InvalidCredentialsError(DomainError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password.")


class AccountLockedError(DomainError):
    def __init__(self, locked_until_iso: str) -> None:
        super().__init__(f"Account is locked until {locked_until_iso}.")
        self.locked_until_iso = locked_until_iso


class AccountNotVerifiedError(DomainError):
    def __init__(self) -> None:
        super().__init__("Account email has not been verified yet.")


class AccountDeactivatedError(DomainError):
    def __init__(self) -> None:
        super().__init__("This account has been deactivated.")


class InvalidTokenError(DomainError):
    def __init__(self, reason: str = "Invalid or expired token.") -> None:
        super().__init__(reason)


class RefreshTokenReuseDetectedError(DomainError):
    """Raised when an already-used (rotated) refresh token is presented again.

    This is a strong signal of token theft: the legitimate client already
    rotated this token, so whoever is presenting it now is not the original
    holder. The caller must revoke every refresh token for the user.
    """

    def __init__(self) -> None:
        super().__init__("Refresh token reuse detected; all sessions have been revoked.")


class WeakPasswordError(DomainError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
