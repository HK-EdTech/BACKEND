from prisma import Prisma
from fastapi import HTTPException, status
from uuid import UUID
from typing import Optional


class AuthService:
    def __init__(self, db: Prisma):
        self.db = db

    async def create_profile(
        self,
        user_id: UUID,
        first_name: str,
        surname: str,
        username: str,
        role_name: str,
        class_level: Optional[str] = None,
        organization_id: Optional[UUID] = None,
    ):
        """Create user profile after Supabase auth"""

        # Check if profile already exists
        existing_profile = await self.db.profiles.find_unique(
            where={"id": str(user_id)}
        )
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile already exists for this user"
            )

        # Validate role exists in roles table
        role = await self.db.roles.find_unique(
            where={"name": role_name}
        )
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: '{role_name}'. Must be 'student', 'teacher', or 'private_tutor'"
            )

        # Create profile
        profile = await self.db.profiles.create(
            data={
                "id": str(user_id),
                "first_name": first_name,
                "surname": surname,
                "username": username,
                "class_level": class_level,
                "organization_id": str(organization_id) if organization_id else None,
            }
        )

        # Create profile_roles relationship
        await self.db.profile_roles.create(
            data={
                "profile_id": str(user_id),
                "role_id": role.id,
            }
        )

        return profile
