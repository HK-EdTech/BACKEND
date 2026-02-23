from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends

from ...database import prisma_client
from ...deps import get_current_user
from .homework_service import HomeworkService
from .pydantic_model.homework_pydantic_model import TeacherHomeworkResponse

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
