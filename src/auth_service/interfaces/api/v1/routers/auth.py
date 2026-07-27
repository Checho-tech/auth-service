"""Authentication endpoints: register, verify, login, refresh, logout, password management."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from auth_service.application.services.auth_service import AuthService
from auth_service.domain.entities import UserEntity
from auth_service.domain.exceptions import (
    AccountDeactivatedError,
    AccountLockedError,
    AccountNotVerifiedError,
    DomainError,
    InvalidCredentialsError,
    InvalidTokenError,
    RefreshTokenReuseDetectedError,
    UserAlreadyExistsError,
    WeakPasswordError,
)
from auth_service.infrastructure.config import get_settings
from auth_service.infrastructure.rate_limiting import limiter
from auth_service.interfaces.api.dependencies import get_auth_service, get_current_user
from auth_service.interfaces.api.v1.schemas.auth_schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Maps domain exceptions to HTTP responses in one place, so the service
# layer never has to know what an HTTP status code is.
_ERROR_STATUS_MAP: dict[type[DomainError], int] = {
    UserAlreadyExistsError: status.HTTP_409_CONFLICT,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    AccountLockedError: status.HTTP_423_LOCKED,
    AccountNotVerifiedError: status.HTTP_403_FORBIDDEN,
    AccountDeactivatedError: status.HTTP_403_FORBIDDEN,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    RefreshTokenReuseDetectedError: status.HTTP_401_UNAUTHORIZED,
    WeakPasswordError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def _raise_as_http(exc: DomainError) -> None:
    status_code = _ERROR_STATUS_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)
    raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    try:
        await auth_service.register(body.email, body.password, body.full_name)
    except DomainError as exc:
        _raise_as_http(exc)
    return MessageResponse(
        message="Registration successful. Check your email to verify your account."
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    body: VerifyEmailRequest, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    try:
        await auth_service.verify_email(body.token)
    except DomainError as exc:
        _raise_as_http(exc)
    return MessageResponse(message="Email verified successfully.")


@router.post("/login", response_model=TokenResponse)
@limiter.limit(get_settings().rate_limit_login)
async def login(
    request: Request, body: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    try:
        pair = await auth_service.login(
            body.email,
            body.password,
            request.client.host if request.client else None,
            request.headers.get("user-agent"),
        )
    except DomainError as exc:
        _raise_as_http(exc)
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request, body: RefreshRequest, auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    try:
        pair = await auth_service.refresh(body.refresh_token, request.headers.get("user-agent"))
    except DomainError as exc:
        _raise_as_http(exc)
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: LogoutRequest, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    await auth_service.logout(body.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit(get_settings().rate_limit_login)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.request_password_reset(body.email)
    # Always the same message, whether or not the email exists — prevents
    # user enumeration via response differences.
    return MessageResponse(
        message="If that email is registered, a reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    body: ResetPasswordRequest, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    try:
        await auth_service.reset_password(body.token, body.new_password)
    except DomainError as exc:
        _raise_as_http(exc)
    return MessageResponse(message="Password has been reset successfully.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user: UserEntity = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        await auth_service.change_password(current_user.id, body.old_password, body.new_password)
    except DomainError as exc:
        _raise_as_http(exc)
    return MessageResponse(message="Password changed successfully. Please log in again.")
