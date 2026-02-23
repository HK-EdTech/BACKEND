from prisma import Prisma
from fastapi import HTTPException, status
from uuid import UUID
from typing import Optional


class ProfileService:
    def __init__(self, db: Prisma):
        self.db = db

    async def get_profile_by_id(self, user_id: UUID):
        """Get profile by auth user ID with role info"""
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
        avatar_url: Optional[str] = None,
    ):
        """Update base user profile (no role changes)"""
        update_data = {}
        if first_name is not None:
            update_data["first_name"] = first_name
        if surname is not None:
            update_data["surname"] = surname
        if username is not None:
            update_data["username"] = username
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url

        profile = await self.db.profiles.update(
            where={"id": str(user_id)},
            data=update_data
        )
        return profile

    async def get_student_profile(self, user_id: UUID):
        """Get student-specific profile with enrollments"""
        student_profile = await self.db.student_profiles.find_unique(
            where={"id": str(user_id)},
            include={
                "profile": True,
                "enrollments": {
                    "include": {
                        "classes": True
                    }
                }
            }
        )
        if not student_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        return student_profile

    async def update_student_level(self, user_id: UUID, level: str):
        """Update student's class level"""
        return await self.db.student_profiles.update(
            where={"id": str(user_id)},
            data={"level": level}
        )

    async def get_teacher_profile(self, user_id: UUID):
        """Get teacher-specific profile with classes"""
        teacher_profile = await self.db.teacher_profiles.find_unique(
            where={"id": str(user_id)},
            include={
                "profile": True,
                "classes": True
            }
        )
        if not teacher_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher profile not found"
            )
        return teacher_profile

    async def update_teacher_bio(self, user_id: UUID, bio: Optional[str]):
        """Update teacher bio"""
        return await self.db.teacher_profiles.update(
            where={"id": str(user_id)},
            data={"bio": bio}
        )
