from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from prisma import Prisma


class HomeworkService:
    """Service for homework read/write operations"""

    CLASS_HOMEWORK_TYPE = "class"
    ONETIME_HOMEWORK_TYPE = "onetime"

    def __init__(self, db: Prisma):
        self.db = db

    @classmethod
    def _normalize_homework_type(cls, homework_type: Optional[str]) -> Optional[str]:
        if homework_type is None:
            return None

        normalized = str(homework_type).strip().lower()
        if not normalized:
            return None

        if normalized in {"class", "assignable"}:
            return cls.CLASS_HOMEWORK_TYPE

        if normalized in {"onetime", "one_time"}:
            return cls.ONETIME_HOMEWORK_TYPE

        return None

    @classmethod
    def _get_homework_type_value(cls, homework_type: Optional[str]) -> Optional[str]:
        normalized = cls._normalize_homework_type(homework_type)
        if normalized:
            return normalized
        if homework_type is None:
            return None
        fallback = str(homework_type).strip().lower()
        if not fallback:
            return None
        return fallback

    @classmethod
    def _is_valid_homework_type(cls, homework_type: str) -> bool:
        return homework_type in {
            cls.CLASS_HOMEWORK_TYPE,
            cls.ONETIME_HOMEWORK_TYPE,
        }

    @classmethod
    def _default_homework_type(cls) -> str:
        return cls.CLASS_HOMEWORK_TYPE

    async def _ensure_teacher_profile(self, user_id: UUID):
        teacher_profile = await self.db.teacher_profiles.find_unique(
            where={"id": str(user_id)}
        )

        if not teacher_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teacher accounts can access teacher homework",
            )

    @staticmethod
    def _dedupe_class_ids(class_ids: List[UUID]) -> List[str]:
        unique: List[str] = []
        seen = set()
        for class_id in class_ids:
            class_id_str = str(class_id)
            if class_id_str in seen:
                continue
            seen.add(class_id_str)
            unique.append(class_id_str)
        return unique

    async def _validate_owned_classes(self, user_id: UUID, class_ids: List[UUID]) -> List[str]:
        class_id_values = self._dedupe_class_ids(class_ids)

        for class_id in class_id_values:
            class_record = await self.db.classes.find_unique(where={"id": class_id})
            if not class_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Class not found: {class_id}",
                )
            if class_record.teacher_id != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only assign homework to your own classes",
                )

        return class_id_values

    async def _get_homework_or_404_for_teacher(self, user_id: UUID, homework_id: UUID):
        homework = await self.db.homework.find_first(
            where={
                "id": str(homework_id),
                "teacher_id": str(user_id),
            },
        )

        if not homework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Homework not found",
            )

        return homework

    async def _replace_homework_classes(
        self,
        homework_id: str,
        user_id: UUID,
        class_ids: List[str],
    ):
        await self.db.homework_classes.delete_many(
            where={"homework_id": homework_id}
        )

        for class_id in class_ids:
            await self.db.homework_classes.create(
                data={
                    "homework_id": homework_id,
                    "class_id": class_id,
                    "assign_by": str(user_id),
                }
            )

    async def _get_homework_with_relations(self, homework_id: str):
        return await self.db.homework.find_unique(
            where={"id": homework_id},
            include={
                "classes": {
                    "include": {
                        "enrollments": True,
                    }
                },
                "homework_classes": {
                    "include": {
                        "classes": {
                            "include": {
                                "enrollments": True,
                            }
                        }
                    }
                },
            },
        )

    @classmethod
    def _to_teacher_homework_response(cls, item) -> dict:
        class_links = []
        seen = set()

        for link in item.homework_classes or []:
            class_record = link.classes
            if not class_record:
                continue
            if class_record.id in seen:
                continue
            seen.add(class_record.id)
            class_links.append(class_record)

        assigned_students = 0
        for class_record in class_links:
            assigned_students += len(class_record.enrollments or [])

        first_class = class_links[0] if class_links else None
        homework_type_raw = getattr(item, "homework_type", None)
        homework_type_value = cls._get_homework_type_value(homework_type_raw)

        return {
            "id": item.id,
            "title": item.title,
            "subject": item.subject,
            "class_id": first_class.id if first_class else None,
            "class_name": first_class.name if first_class else None,
            "due_date": item.due_date,
            "full_score": item.full_score,
            "homework_type": homework_type_value,
            "homework_type_value": homework_type_value,
            "assigned_classes": len(class_links),
            "assigned_class_ids": [class_record.id for class_record in class_links],
            "assigned_students": assigned_students,
            "created_at": item.created_at,
        }

    async def get_teacher_homework(self, user_id: UUID) -> List[dict]:
        """Get homework created by the authenticated teacher"""
        await self._ensure_teacher_profile(user_id)

        records = await self.db.homework.find_many(
            where={"teacher_id": str(user_id)},
            include={
                "classes": {
                    "include": {
                        "enrollments": True
                    }
                },
                "homework_classes": {
                    "include": {
                        "classes": {
                            "include": {
                                "enrollments": True
                            }
                        }
                    }
                },
            },
            order={"created_at": "desc"},
        )

        return [self._to_teacher_homework_response(item) for item in records]

    async def create_teacher_homework(
        self,
        user_id: UUID,
        title: str,
        subject: Optional[str] = None,
        due_date=None,
        full_score: Optional[float] = None,
        homework_type: Optional[str] = None,
        class_ids: Optional[List[UUID]] = None,
    ) -> dict:
        """Create homework and assignment rows in homework_classes"""
        await self._ensure_teacher_profile(user_id)

        class_ids = class_ids or []
        validated_class_ids = await self._validate_owned_classes(user_id, class_ids)
        if homework_type is None:
            homework_type_value = self._default_homework_type()
        else:
            homework_type_value = self._normalize_homework_type(homework_type)

        if not homework_type_value or not self._is_valid_homework_type(homework_type_value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid homework_type value. Expected 'class' or 'onetime'.",
            )

        created = await self.db.homework.create(
            data={
                "title": title.strip(),
                "subject": subject.strip() if subject else None,
                "teacher_id": str(user_id),
                "due_date": due_date,
                "full_score": full_score,
                "homework_type": homework_type_value,
            }
        )

        await self._replace_homework_classes(created.id, user_id, validated_class_ids)

        created_with_relations = await self._get_homework_with_relations(created.id)
        return self._to_teacher_homework_response(created_with_relations)

    async def assign_homework_to_classes(
        self,
        user_id: UUID,
        homework_id: UUID,
        class_ids: List[UUID],
    ) -> dict:
        """Re-assign homework to class list via homework_classes"""
        await self._ensure_teacher_profile(user_id)
        await self._get_homework_or_404_for_teacher(user_id, homework_id)

        validated_class_ids = await self._validate_owned_classes(user_id, class_ids or [])
        if not validated_class_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please select at least one class",
            )

        await self._replace_homework_classes(str(homework_id), user_id, validated_class_ids)

        await self.db.homework.update(
            where={"id": str(homework_id)},
            data={"class_id": None},
        )

        updated_with_relations = await self._get_homework_with_relations(str(homework_id))
        return self._to_teacher_homework_response(updated_with_relations)
