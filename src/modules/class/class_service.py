from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from prisma import Prisma


class ClassService:
    """Service for class CRUD operations"""

    def __init__(self, db: Prisma):
        self.db = db

    @staticmethod
    def _display_name(profile) -> str:
        if not profile:
            return "Unknown"

        if getattr(profile, "full_name", None):
            return profile.full_name

        first = (getattr(profile, "first_name", "") or "").strip()
        surname = (getattr(profile, "surname", "") or "").strip()
        full = f"{first} {surname}".strip()
        if full:
            return full

        return getattr(profile, "username", "Unknown") or "Unknown"

    async def _get_class_or_404(self, class_id: UUID, include: Optional[dict] = None):
        class_record = await self.db.classes.find_unique(
            where={"id": str(class_id)},
            include=include,
        )

        if not class_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found",
            )

        return class_record

    async def _ensure_can_view_class(self, user_id: UUID, class_id: UUID, teacher_id: str):
        if teacher_id == str(user_id):
            return

        enrollment = await self.db.enrollments.find_first(
            where={
                "student_id": str(user_id),
                "class_id": str(class_id),
            }
        )

        if enrollment:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this class",
        )

    async def _ensure_teacher_owns_class(self, user_id: UUID, class_id: UUID):
        teacher_profile = await self.db.teacher_profiles.find_unique(
            where={"id": str(user_id)}
        )

        if not teacher_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teacher accounts can perform this action",
            )

        class_record = await self._get_class_or_404(class_id)

        if class_record.teacher_id != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the class teacher can perform this action",
            )

        return class_record

    async def _get_teacher_organization_id(self, user_id: UUID, class_record=None) -> str:
        profile = await self.db.profiles.find_unique(where={"id": str(user_id)})

        organization_id = profile.organization_id if profile else None
        if not organization_id and class_record:
            organization_id = class_record.organization_id

        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher account is not linked to an organization",
            )

        return organization_id

    @staticmethod
    def _dedupe_ids(values: List[str]) -> List[str]:
        seen = set()
        result = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    @staticmethod
    def _to_class_student_response(student_profile, enrollment):
        profile = student_profile.profile
        return {
            "id": profile.id,
            "full_name": ClassService._display_name(profile),
            "username": profile.username,
            "avatar_url": profile.avatar_url,
            "class_level": student_profile.level,
            "status": "active",
            "enrolled_at": enrollment.enrollment_date,
        }

    async def get_all_classes(self):
        """Get all classes from public.classes"""
        return await self.db.classes.find_many(order={"created_at": "desc"})

    async def get_teacher_classes(self, user_id: UUID):
        """Get all classes for the authenticated teacher"""
        teacher_profile = await self.db.teacher_profiles.find_unique(
            where={"id": str(user_id)}
        )

        if not teacher_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teacher accounts can access teacher classes",
            )

        return await self.db.classes.find_many(
            where={"teacher_id": str(user_id)},
            order={"created_at": "desc"},
        )

    async def get_student_classes(self, user_id: UUID):
        """Get all classes enrolled by the authenticated student"""
        student_profile = await self.db.student_profiles.find_unique(
            where={"id": str(user_id)},
            include={
                "enrollments": {
                    "include": {
                        "classes": True
                    }
                }
            }
        )

        if not student_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only student accounts can access enrolled classes",
            )

        classes: List = [
            enrollment.classes for enrollment in student_profile.enrollments if enrollment.classes
        ]

        classes.sort(key=lambda c: c.created_at, reverse=True)
        return classes

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

    async def get_class_detail(self, user_id: UUID, class_id: UUID):
        """Get class header detail for classroom page"""
        class_record = await self._get_class_or_404(
            class_id,
            include={
                "educational_organizations": True,
                "teacher_profile": {"include": {"profile": True}},
                "enrollments": True,
            },
        )

        await self._ensure_can_view_class(user_id, class_id, class_record.teacher_id)

        teacher_name = self._display_name(
            class_record.teacher_profile.profile if class_record.teacher_profile else None
        )

        return {
            "id": class_record.id,
            "name": class_record.name,
            "subject": class_record.subject,
            "target_level": class_record.target_level,
            "organization_id": class_record.organization_id,
            "organization_name": class_record.educational_organizations.name
            if class_record.educational_organizations
            else None,
            "teacher_id": class_record.teacher_id,
            "teacher_name": teacher_name,
            "num_students": len(class_record.enrollments),
            "created_at": class_record.created_at,
        }

    async def get_class_homework(self, user_id: UUID, class_id: UUID):
        """Get homeworks under a class using homework_classes relation"""
        class_record = await self._get_class_or_404(
            class_id,
            include={"enrollments": True},
        )

        await self._ensure_can_view_class(user_id, class_id, class_record.teacher_id)

        assigned_students = len(class_record.enrollments)
        assignments = await self.db.homework_classes.find_many(
            where={"class_id": str(class_id)},
            include={"homework": True},
            order={"created_at": "desc"},
        )

        result = []
        seen_homework_ids = set()

        for assignment in assignments:
            homework = assignment.homework
            if not homework:
                continue
            if homework.id in seen_homework_ids:
                continue

            seen_homework_ids.add(homework.id)
            result.append(
                {
                    "id": homework.id,
                    "title": homework.title,
                    "subject": homework.subject,
                    "class_id": str(class_id),
                    "due_date": homework.due_date,
                    "assigned_students": assigned_students,
                    "created_at": homework.created_at,
                }
            )

        return result

    async def create_class_homework(
        self,
        user_id: UUID,
        class_id: UUID,
        title: str,
        subject: Optional[str] = None,
        due_date=None,
        full_score: Optional[float] = None,
    ):
        """Create homework under a class and assignment in homework_classes"""
        class_record = await self._ensure_teacher_owns_class(user_id, class_id)

        created = await self.db.homework.create(
            data={
                "title": title.strip(),
                "subject": (subject.strip() if subject else class_record.subject),
                "class_id": str(class_id),
                "teacher_id": str(user_id),
                "due_date": due_date,
                "full_score": full_score,
            }
        )

        await self.db.homework_classes.create(
            data={
                "homework_id": created.id,
                "class_id": str(class_id),
                "assign_by": str(user_id),
            }
        )

        enrollments = await self.db.enrollments.find_many(where={"class_id": str(class_id)})

        return {
            "id": created.id,
            "title": created.title,
            "subject": created.subject,
            "class_id": str(class_id),
            "due_date": created.due_date,
            "assigned_students": len(enrollments),
            "created_at": created.created_at,
        }

    async def get_class_students(self, user_id: UUID, class_id: UUID):
        """Get enrolled students under a class"""
        class_record = await self._get_class_or_404(class_id)
        await self._ensure_can_view_class(user_id, class_id, class_record.teacher_id)

        enrollments = await self.db.enrollments.find_many(
            where={"class_id": str(class_id)},
            include={
                "student_profile": {
                    "include": {
                        "profile": True,
                    }
                }
            },
            order={"enrollment_date": "desc"},
        )

        result = []
        for enrollment in enrollments:
            student_profile = enrollment.student_profile
            profile = student_profile.profile if student_profile else None
            if not profile:
                continue

            result.append(
                self._to_class_student_response(student_profile, enrollment)
            )

        return result

    async def get_class_student_candidates(self, user_id: UUID, class_id: UUID):
        """
        List all student profiles in teacher's organization that are not yet
        enrolled in the target class.
        """
        class_record = await self._ensure_teacher_owns_class(user_id, class_id)
        teacher_org_id = await self._get_teacher_organization_id(user_id, class_record)

        enrollments = await self.db.enrollments.find_many(
            where={"class_id": str(class_id)}
        )
        enrolled_student_ids = {enrollment.student_id for enrollment in enrollments}

        profiles = await self.db.profiles.find_many(
            where={"organization_id": teacher_org_id},
            include={"student_profile": True},
            order={"full_name": "asc"},
        )

        result = []
        for profile in profiles:
            student_profile = profile.student_profile
            if not student_profile:
                continue
            if profile.id in enrolled_student_ids:
                continue

            result.append(
                {
                    "id": profile.id,
                    "full_name": self._display_name(profile),
                    "username": profile.username,
                    "avatar_url": profile.avatar_url,
                    "class_level": student_profile.level,
                }
            )

        return result

    async def add_class_student(
        self,
        user_id: UUID,
        class_id: UUID,
        student_ids: Optional[List[UUID]] = None,
        student_id: Optional[UUID] = None,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
    ):
        """
        Enroll one or many existing student profiles into class.

        Supports:
        - bulk mode via student_ids
        - legacy single mode via student_id / username / full_name
        """
        class_record = await self._ensure_teacher_owns_class(user_id, class_id)
        teacher_org_id = await self._get_teacher_organization_id(user_id, class_record)

        candidate_ids: List[str] = []

        if student_ids:
            candidate_ids = [str(value) for value in student_ids]
        elif student_id or username or full_name:
            resolved_student_profile = None

            if student_id:
                resolved_student_profile = await self.db.student_profiles.find_unique(
                    where={"id": str(student_id)},
                    include={"profile": True},
                )

            if not resolved_student_profile and username:
                profile = await self.db.profiles.find_unique(
                    where={"username": username.strip()},
                )
                if profile:
                    resolved_student_profile = await self.db.student_profiles.find_unique(
                        where={"id": profile.id},
                        include={"profile": True},
                    )

            if not resolved_student_profile and full_name:
                profile = await self.db.profiles.find_first(
                    where={"full_name": full_name.strip()},
                )
                if profile:
                    resolved_student_profile = await self.db.student_profiles.find_unique(
                        where={"id": profile.id},
                        include={"profile": True},
                    )

            if not resolved_student_profile or not resolved_student_profile.profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student profile not found",
                )

            candidate_ids = [resolved_student_profile.id]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide student_ids, or one of student_id/username/full_name",
            )

        deduped_candidate_ids = self._dedupe_ids(candidate_ids)
        if len(deduped_candidate_ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No student selected for enrollment",
            )

        student_profiles = await self.db.student_profiles.find_many(
            where={"id": {"in": deduped_candidate_ids}},
            include={"profile": True},
        )

        student_profile_by_id: Dict[str, Any] = {
            student_profile.id: student_profile
            for student_profile in student_profiles
            if student_profile.profile
        }

        missing_ids = [value for value in deduped_candidate_ids if value not in student_profile_by_id]
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more student profiles were not found",
            )

        for value in deduped_candidate_ids:
            profile = student_profile_by_id[value].profile
            if profile.organization_id != teacher_org_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected students must belong to your organization",
                )

        existing_enrollments = await self.db.enrollments.find_many(
            where={
                "class_id": str(class_id),
                "student_id": {"in": deduped_candidate_ids},
            }
        )
        existing_student_ids = {enrollment.student_id for enrollment in existing_enrollments}

        ids_to_enroll = [value for value in deduped_candidate_ids if value not in existing_student_ids]
        if len(ids_to_enroll) == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="All selected students are already enrolled in this class",
            )

        created_enrollments = []
        for value in ids_to_enroll:
            created_enrollments.append(
                await self.db.enrollments.create(
                    data={
                        "class_id": str(class_id),
                        "student_id": value,
                    }
                )
            )

        enrollment_by_student_id = {
            enrollment.student_id: enrollment for enrollment in created_enrollments
        }

        result = []
        for value in ids_to_enroll:
            result.append(
                self._to_class_student_response(
                    student_profile_by_id[value],
                    enrollment_by_student_id[value],
                )
            )

        return result

    async def get_class_teachers(self, user_id: UUID, class_id: UUID):
        """Get teachers associated with class (current schema has single teacher)"""
        class_record = await self._get_class_or_404(class_id)
        await self._ensure_can_view_class(user_id, class_id, class_record.teacher_id)

        teacher_profile = await self.db.teacher_profiles.find_unique(
            where={"id": class_record.teacher_id},
            include={"profile": True},
        )

        if not teacher_profile or not teacher_profile.profile:
            return []

        profile = teacher_profile.profile

        return [{
            "id": profile.id,
            "full_name": self._display_name(profile),
            "username": profile.username,
            "avatar_url": profile.avatar_url,
            "bio": teacher_profile.bio,
        }]
