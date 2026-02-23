from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from prisma import Prisma


class ClassService:
    """Service for class CRUD operations"""

    def __init__(self, db: Prisma):
        self.db = db

    async def get_all_classes(self):
        """Get all classes from public.classes"""
        return await self.db.classes.find_many(order={"created_at": "desc"})

    async def create_class(
        self,
        user_id: UUID,
        name: str,
        subject: str,
        target_level: Optional[str] = None,
        organization_id: Optional[str] = None,
    ):
        """
        Create a class for the authenticated teacher profile.

        teacher_id maps to teacher_profiles.id (same UUID as profile/user).
        """
        teacher_profile = await self.db.teacher_profiles.find_unique(
            where={"id": str(user_id)}
        )

        if not teacher_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teacher accounts can create classes",
            )

        org_id = organization_id

        if org_id is None:
            profile = await self.db.profiles.find_unique(where={"id": str(user_id)})
            if profile:
                org_id = profile.organization_id

        return await self.db.classes.create(
            data={
                "name": name.strip(),
                "subject": subject.strip(),
                "target_level": target_level.strip() if target_level else None,
                "teacher_id": str(user_id),
                "organization_id": org_id,
            }
        )
