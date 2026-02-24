from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TeacherHomeworkResponse(BaseModel):
    """Homework record enriched for teacher dashboard cards"""

    id: UUID
    title: Optional[str] = None
    subject: Optional[str] = None
    class_id: Optional[UUID] = None
    class_name: Optional[str] = None
    due_date: Optional[datetime] = None
    full_score: Optional[float] = None
    assigned_classes: int
    assigned_class_ids: List[UUID] = Field(default_factory=list)
    assigned_students: int
    created_at: datetime

    class Config:
        from_attributes = True


class CreateTeacherHomeworkRequest(BaseModel):
    """Payload to create homework and assign to classes"""

    title: str = Field(..., min_length=1, max_length=200)
    subject: Optional[str] = Field(None, max_length=120)
    due_date: Optional[datetime] = None
    full_score: Optional[float] = Field(None, ge=0)
    class_ids: List[UUID] = Field(default_factory=list)


class AssignHomeworkClassesRequest(BaseModel):
    """Payload to re-assign homework classes"""

    class_ids: List[UUID] = Field(default_factory=list)
