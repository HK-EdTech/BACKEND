from fastapi import APIRouter, Depends
from uuid import UUID
from ...deps import get_current_user
from ...database import prisma_client
from .pydantic_model.profile_pydantic_model import ProfileResponse
from .pydantic_model.update_profile_pydantic_model import ProfileUpdateRequest
from .profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])

def get_profile_service():
    return ProfileService(prisma_client)

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user = Depends(get_current_user),
    profile_service = Depends(get_profile_service)
):
    """Get current user's profile"""
    user_id = UUID(current_user.get("sub"))
    profile = await profile_service.get_profile_by_id(user_id)
    return profile

@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    update_data: ProfileUpdateRequest,
    current_user = Depends(get_current_user),
    profile_service = Depends(get_profile_service)
):
    """Update current user's profile"""
    user_id = UUID(current_user.get("sub"))
    profile = await profile_service.update_profile(
        user_id=user_id,
        first_name=update_data.first_name,
        surname=update_data.surname,
        username=update_data.username,
        class_level=update_data.class_level,
        avatar_url=update_data.avatar_url,
    )
    return profile
