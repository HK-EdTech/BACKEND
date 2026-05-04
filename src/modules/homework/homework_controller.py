from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status

from ...database import prisma_client
from ...deps import get_current_user
from .homework_service import HomeworkService
from .pydantic_model.homework_pydantic_model import (
    AssignHomeworkClassesRequest,
    CreateTeacherHomeworkRequest,
    TeacherHomeworkResponse,
)

router = APIRouter(prefix="/homework", tags=["Homework"])


def get_homework_service():
    return HomeworkService(prisma_client)


@router.get("/me/teacher", response_model=List[TeacherHomeworkResponse])
async def get_my_teacher_homework(
    current_user=Depends(get_current_user),
    homework_service=Depends(get_homework_service),
):
    """Get homework created by authenticated teacher"""
    user_id = UUID(current_user.get("sub"))
    return await homework_service.get_teacher_homework(user_id)


@router.post("/me/teacher", response_model=TeacherHomeworkResponse, status_code=status.HTTP_201_CREATED)
async def create_my_teacher_homework(
    payload: CreateTeacherHomeworkRequest,
    current_user=Depends(get_current_user),
    homework_service=Depends(get_homework_service),
):
    """Create teacher homework and assign to classes"""
    user_id = UUID(current_user.get("sub"))
    return await homework_service.create_teacher_homework(
        user_id=user_id,
        title=payload.title,
        subject=payload.subject,
        due_date=payload.due_date,
        full_score=payload.full_score,
        homework_type=payload.homework_type,
        class_ids=payload.class_ids,
    )


@router.patch("/{homework_id}/classes", response_model=TeacherHomeworkResponse)
async def assign_homework_to_classes(
    homework_id: UUID,
    payload: AssignHomeworkClassesRequest,
    current_user=Depends(get_current_user),
    homework_service=Depends(get_homework_service),
):
    """Re-assign homework to classes"""
    user_id = UUID(current_user.get("sub"))
    return await homework_service.assign_homework_to_classes(
        user_id=user_id,
        homework_id=homework_id,
        class_ids=payload.class_ids,
    )
