"""User profile endpoints."""

from fastapi import APIRouter, Depends

from auth_service.domain.entities import UserEntity
from auth_service.interfaces.api.dependencies import get_current_user
from auth_service.interfaces.api.v1.schemas.auth_schemas import UserProfileResponse

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: UserEntity = Depends(get_current_user),
) -> UserProfileResponse:
    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        roles=list(current_user.role_names),
    )
