from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import Optional, Union
from ...deps import get_current_user
from ...database import prisma_client
from .pydantic_model.profile_pydantic_model import ProfileResponse
from .pydantic_model.update_profile_pydantic_model import ProfileUpdateRequest
from .profile_service import ProfileService
from ..module.module_service import ModuleService
from ..module.pydantic_model.module_pydantic_model import ProfileWithModulesResponse, ModuleWithPermissions

router = APIRouter(prefix="/profile", tags=["Profile"])

def get_profile_service():
    return ProfileService(prisma_client)

def get_module_service():
    return ModuleService(prisma_client)

@router.get("/me", response_model=Union[ProfileResponse, ProfileWithModulesResponse])
async def get_my_profile(
    include: Optional[str] = Query(None, description="Include related data: 'modules'"),
    current_user = Depends(get_current_user),
    profile_service = Depends(get_profile_service),
    module_service = Depends(get_module_service)
):
    """
    Get current user's profile.

    Query Parameters:
    - include=modules: Returns profile + accessible modules in single response

    Examples:
    - GET /profile/me -> Returns ProfileResponse
    - GET /profile/me?include=modules -> Returns ProfileWithModulesResponse
    """
    user_id = UUID(current_user.get("sub"))
    profile = await profile_service.get_profile_by_id(user_id)

    # Check if modules should be included
    if include == "modules":
        modules = await module_service.get_user_modules_with_permissions(str(user_id))
        return ProfileWithModulesResponse(
            profile=profile.model_dump(),
            modules=[ModuleWithPermissions(**m) for m in modules]
        )

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
