from prisma import Prisma
from fastapi import HTTPException, status
from uuid import UUID
from typing import Optional


class ProfileService:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_profile_by_id(self, user_id: UUID):
        """Get profile by auth user ID with role"""
        profile = await self.db.profiles.find_unique(
            where={"id": str(user_id)},
            include={
                "profile_roles": {
                    "include": {"roles": True}
                }
            }
        )
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found. Please contact support."
            )
        return profile

    async def update_profile(
        self,
        user_id: UUID,
        first_name: Optional[str] = None,
        surname: Optional[str] = None,
        username: Optional[str] = None,
        class_level: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ):
        """Update user profile (no role changes)"""
        update_data = {}
        if first_name is not None:
            update_data["first_name"] = first_name
        if surname is not None:
            update_data["surname"] = surname
        if username is not None:
            update_data["username"] = username
        if class_level is not None:
            update_data["class_level"] = class_level
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url

        profile = await self.db.profiles.update(
            where={"id": str(user_id)},
            data=update_data
        )
        return profile
