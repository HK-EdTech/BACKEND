from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status

from ...database import prisma_client
from ...deps import get_current_user
from .class_service import ClassService
from .pydantic_model.class_pydantic_model import ClassResponse, CreateClassRequest

router = APIRouter(prefix="/class", tags=["Class"])


def get_class_service():
    return ClassService(prisma_client)


@router.get("", response_model=List[ClassResponse])
async def get_classes(class_service=Depends(get_class_service)):
    """Get all classes from classes table"""
    return await class_service.get_all_classes()




@router.get("/me/teacher", response_model=List[ClassResponse])
async def get_my_teacher_classes(
    current_user=Depends(get_current_user),
    class_service=Depends(get_class_service),
):
    """Get classes taught by authenticated teacher"""
    user_id = UUID(current_user.get("sub"))
    return await class_service.get_teacher_classes(user_id)


@router.get("/me/student", response_model=List[ClassResponse])
async def get_my_student_classes(
    current_user=Depends(get_current_user),
    class_service=Depends(get_class_service),
):
    """Get classes enrolled by authenticated student"""
    user_id = UUID(current_user.get("sub"))
    return await class_service.get_student_classes(user_id)

@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: CreateClassRequest,
    current_user=Depends(get_current_user),
    class_service=Depends(get_class_service),
):
    """Create class record for authenticated teacher"""
    user_id = UUID(current_user.get("sub"))
    created = await class_service.create_class(
        user_id=user_id,
        name=payload.name,
        subject=payload.subject,
        target_level=payload.target_level,
        organization_id=str(payload.organization_id) if payload.organization_id else None,
    )
    return created
