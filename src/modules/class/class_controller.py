from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from ...database import prisma_client
from .class_service import ClassService
from .pydantic_model.class_pydantic_model import (
    AddClassStudentRequest,
    ClassCandidateStudentResponse,
    ClassDetailResponse,
    ClassHomeworkResponse,
    ClassHomeworkSubmissionResponse,
    ClassManagementResponse,
    ClassResponse,
    ClassStudentResponse,
    ClassTeacherResponse,
    CreateClassHomeworkRequest,
    CreateClassRequest,
)

router = APIRouter(prefix="/class", tags=["Class"])


def get_class_service():
    return ClassService(prisma_client)


@router.get("", response_model=List[ClassResponse])
async def get_classes(class_service=Depends(get_class_service)):
    """Get all classes from classes table"""
    return await class_service.get_all_classes()


@router.get("/me/teacher", response_model=List[ClassResponse])
async def get_my_teacher_classes(
    request: Request,
    class_service=Depends(get_class_service),
):
    """Get classes taught by authenticated teacher"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.get_teacher_classes(user_id)


@router.get("/me/teacher/management", response_model=ClassManagementResponse)
async def get_my_teacher_class_management(
    request: Request,
    class_service=Depends(get_class_service),
):
    """Get grouped class management data for authenticated teacher"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.get_class_management(user_id)


@router.get("/me/student", response_model=List[ClassResponse])
async def get_my_student_classes(
    request: Request,
    class_service=Depends(get_class_service),
):
    """Get classes enrolled by authenticated student"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.get_student_classes(user_id)


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: CreateClassRequest,
    request: Request,
    class_service=Depends(get_class_service),
):
    """Create class record for authenticated teacher"""
    user_id = UUID(request.state.user.get("sub"))
    created = await class_service.create_class(
        user_id=user_id,
        name=payload.name,
        subject=payload.subject,
        target_level=payload.target_level,
        organization_id=str(payload.organization_id) if payload.organization_id else None,
    )
    return created


@router.get("/{class_id}", response_model=ClassDetailResponse)
async def get_class_detail(
    class_id: UUID,
    request: Request,
    class_service=Depends(get_class_service),
):
    """Get class details by class_id"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.get_class_detail(user_id=user_id, class_id=class_id)


@router.get("/{class_id}/homework", response_model=List[ClassHomeworkResponse])
async def get_class_homework(
    class_id: UUID,
    request: Request,
    class_service=Depends(get_class_service),
):
    """Get homework under a class"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.get_class_homework(user_id=user_id, class_id=class_id)


@router.get("/{class_id}/homework/{homework_id}/submissions", response_model=List[ClassHomeworkSubmissionResponse])
async def get_class_homework_submissions(
    class_id: UUID,
    homework_id: UUID,
    request: Request,
    class_service=Depends(get_class_service),
):
    """Get homework submissions under a class (teacher only)"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.get_class_homework_submissions(
        user_id=user_id,
        class_id=class_id,
        homework_id=homework_id,
    )


@router.post("/{class_id}/homework", response_model=ClassHomeworkResponse, status_code=status.HTTP_201_CREATED)
async def create_class_homework(
    class_id: UUID,
    payload: CreateClassHomeworkRequest,
    request: Request,
    class_service=Depends(get_class_service),
):
    """Create homework under a class"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.create_class_homework(
        user_id=user_id,
        class_id=class_id,
        title=payload.title,
        subject=payload.subject,
        due_date=payload.due_date,
        full_score=payload.full_score,
    )


@router.get("/{class_id}/students", response_model=List[ClassStudentResponse])
async def get_class_students(
    class_id: UUID,
    request: Request,
    class_service=Depends(get_class_service),
):
    """Get students under a class"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.get_class_students(user_id=user_id, class_id=class_id)


@router.get("/{class_id}/students/candidates", response_model=List[ClassCandidateStudentResponse])
async def get_class_student_candidates(
    class_id: UUID,
    request: Request,
    class_service=Depends(get_class_service),
):
    """Get candidate students from teacher organization (excluding enrolled)"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.get_class_student_candidates(user_id=user_id, class_id=class_id)


@router.post("/{class_id}/students", response_model=List[ClassStudentResponse], status_code=status.HTTP_201_CREATED)
async def add_class_student(
    class_id: UUID,
    payload: AddClassStudentRequest,
    request: Request,
    class_service=Depends(get_class_service),
):
    """Enroll a student into a class"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.add_class_student(
        user_id=user_id,
        class_id=class_id,
        student_ids=payload.student_ids,
        student_id=payload.student_id,
        username=payload.username,
        full_name=payload.full_name,
    )


@router.get("/{class_id}/teachers", response_model=List[ClassTeacherResponse])
async def get_class_teachers(
    class_id: UUID,
    request: Request,
    class_service=Depends(get_class_service),
):
    """Get teachers under a class"""
    user_id = UUID(request.state.user.get("sub"))
    return await class_service.get_class_teachers(user_id=user_id, class_id=class_id)
