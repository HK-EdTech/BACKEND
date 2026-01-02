from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from ...deps import get_current_user
from ...database import prisma_client
from .pydantic_model.signup_pydantic_model import SignupRequest
from ..profile.pydantic_model.profile_pydantic_model import ProfileResponse
from .auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_auth_service():
    return AuthService(prisma_client)

@router.post("/signup", response_model=ProfileResponse)
async def signup(
    signup_data: SignupRequest,
    current_user = Depends(get_current_user),
    auth_service = Depends(get_auth_service)
):
    """Create user profile after Supabase auth"""
    # Verify JWT user_id matches request
    jwt_user_id = UUID(current_user.get("sub"))
    if jwt_user_id != signup_data.user_id:
        raise HTTPException(
            status_code=403,
            detail="User ID mismatch"
        )

    profile = await auth_service.create_profile(
        user_id=signup_data.user_id,
        first_name=signup_data.first_name,
        surname=signup_data.surname,
        username=signup_data.username,
        role_name=signup_data.role_name,
        class_level=signup_data.class_level,
        organization_id=signup_data.organization_id,
    )
    return profile
