from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ClassResponse(BaseModel):
    """Class record from public.classes"""

    id: UUID
    name: str
    subject: str
    target_level: Optional[str] = None
    teacher_id: UUID
    organization_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreateClassRequest(BaseModel):
    """Payload for creating a class"""

    name: str = Field(..., min_length=1, max_length=120)
    subject: str = Field(..., min_length=1, max_length=120)
    target_level: Optional[str] = Field(None, max_length=50)
    organization_id: Optional[UUID] = None


class ClassDetailResponse(BaseModel):
    """Classroom summary response for /class/{id}"""

    id: UUID
    name: str
    subject: str
    target_level: Optional[str] = None
    organization_id: Optional[UUID] = None
    organization_name: Optional[str] = None
    teacher_id: UUID
    teacher_name: str
    num_students: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClassHomeworkResponse(BaseModel):
    """Homework records for a classroom"""

    id: UUID
    title: Optional[str] = None
    subject: Optional[str] = None
    class_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    assigned_students: int
    created_at: datetime

    class Config:
        from_attributes = True


class CreateClassHomeworkRequest(BaseModel):
    """Payload to create homework for a classroom"""

    title: str = Field(..., min_length=1, max_length=200)
    subject: Optional[str] = Field(None, max_length=120)
    due_date: Optional[datetime] = None
    full_score: Optional[float] = Field(None, ge=0)


class ClassStudentResponse(BaseModel):
    """Student item shown in classroom students tab"""

    id: UUID
    full_name: str
    username: str
    avatar_url: Optional[str] = None
    class_level: Optional[str] = None
    status: str
    enrolled_at: datetime

    class Config:
        from_attributes = True


class AddClassStudentRequest(BaseModel):
    """Payload to enroll an existing student into a classroom"""

    student_ids: Optional[List[UUID]] = None
    student_id: Optional[UUID] = None
    username: Optional[str] = Field(None, max_length=120)
    full_name: Optional[str] = Field(None, max_length=240)


class ClassCandidateStudentResponse(BaseModel):
    """Student candidates from teacher's organization for class enrollment"""

    id: UUID
    full_name: str
    username: str
    avatar_url: Optional[str] = None
    class_level: Optional[str] = None

    class Config:
        from_attributes = True


class ClassTeacherResponse(BaseModel):
    """Teacher item shown in classroom teachers tab"""

    id: UUID
    full_name: str
    username: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True
