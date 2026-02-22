from fastapi import APIRouter, Depends, Query, Request
from uuid import UUID
from typing import Optional, Union
import asyncio
from ...database import prisma_client
from .pydantic_model.profile_pydantic_model import ProfileResponse, StudentProfileResponse, TeacherProfileResponse
from .pydantic_model.update_profile_pydantic_model import ProfileUpdateRequest, StudentProfileUpdateRequest, TeacherProfileUpdateRequest
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
    request: Request,
    include: Optional[str] = Query(None, description="Include related data: 'modules'"),
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
    user_id = UUID(request.state.user.get("sub"))

    # Fetch profile and modules in parallel when modules are requested
    if include == "modules":
        profile, modules = await asyncio.gather(
            profile_service.get_profile_by_id(user_id),
            module_service.get_user_modules_with_permissions(str(user_id))
        )
    else:
        profile = await profile_service.get_profile_by_id(user_id)
        modules = None

    # Transform profile: extract role_name and default_route from profile_roles
    profile_dict = profile.model_dump()

    if profile.profile_roles and len(profile.profile_roles) > 0:
        user_role = profile.profile_roles[0].roles
        profile_dict["role_name"] = user_role.name
        profile_dict["default_route"] = user_role.default_route
    else:
        profile_dict["role_name"] = None
        profile_dict["default_route"] = None

    profile_dict["organization_id"] = profile.organization_id
    profile_dict.pop("profile_roles", None)

    if modules is not None:
        return ProfileWithModulesResponse(
            profile=profile_dict,
            modules=[ModuleWithPermissions(**m) for m in modules]
        )

    return ProfileResponse(**profile_dict)

@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    request: Request,
    update_data: ProfileUpdateRequest,
    profile_service = Depends(get_profile_service)
):
    """Update current user's base profile (name, username, avatar)"""
    user_id = UUID(request.state.user.get("sub"))
    profile = await profile_service.update_profile(
        user_id=user_id,
        first_name=update_data.first_name,
        surname=update_data.surname,
        username=update_data.username,
        avatar_url=update_data.avatar_url,
    )
    return profile

@router.get("/me/student", response_model=StudentProfileResponse)
async def get_my_student_profile(
    request: Request,
    profile_service = Depends(get_profile_service)
):
    """Get current user's student profile with enrollments"""
    user_id = UUID(request.state.user.get("sub"))
    return await profile_service.get_student_profile(user_id)

@router.put("/me/student", response_model=StudentProfileResponse)
async def update_my_student_profile(
    request: Request,
    update_data: StudentProfileUpdateRequest,
    profile_service = Depends(get_profile_service)
):
    """Update current user's student profile (class level)"""
    user_id = UUID(request.state.user.get("sub"))
    if update_data.level is not None:
        await profile_service.update_student_level(user_id, update_data.level)
    return await profile_service.get_student_profile(user_id)

@router.get("/me/teacher", response_model=TeacherProfileResponse)
async def get_my_teacher_profile(
    request: Request,
    profile_service = Depends(get_profile_service)
):
    """Get current user's teacher profile with classes"""
    user_id = UUID(request.state.user.get("sub"))
    return await profile_service.get_teacher_profile(user_id)

@router.put("/me/teacher", response_model=TeacherProfileResponse)
async def update_my_teacher_profile(
    request: Request,
    update_data: TeacherProfileUpdateRequest,
    profile_service = Depends(get_profile_service)
):
    """Update current user's teacher profile (bio)"""
    user_id = UUID(request.state.user.get("sub"))
    if update_data.bio is not None:
        await profile_service.update_teacher_bio(user_id, update_data.bio)
    return await profile_service.get_teacher_profile(user_id)
