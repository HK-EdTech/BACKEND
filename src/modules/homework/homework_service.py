from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from prisma import Prisma


class HomeworkService:
    """Service for homework read operations"""

    def __init__(self, db: Prisma):
        self.db = db

    async def get_teacher_homework(self, user_id: UUID) -> List[dict]:
        """Get homework created by the authenticated teacher"""
        teacher_profile = await self.db.teacher_profiles.find_unique(
            where={"id": str(user_id)}
        )

        if not teacher_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teacher accounts can access teacher homework",
            )

        records = await self.db.homework.find_many(
            where={"teacher_id": str(user_id)},
            include={
                "classes": {
                    "include": {
                        "enrollments": True
                    }
                }
            },
            order={"created_at": "desc"},
        )

        result = []
        for item in records:
            assigned_students = len(item.classes.enrollments) if item.classes else 0
            result.append({
                "id": item.id,
                "title": item.title,
                "subject": item.subject,
                "class_id": item.class_id,
                "class_name": item.classes.name if item.classes else None,
                "due_date": item.due_date,
                "assigned_classes": 1 if item.class_id else 0,
                "assigned_students": assigned_students,
                "created_at": item.created_at,
            })

        return result
