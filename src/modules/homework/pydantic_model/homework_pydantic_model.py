from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TeacherHomeworkResponse(BaseModel):
    """Homework record enriched for teacher dashboard cards"""

    id: UUID
    title: Optional[str] = None
    subject: Optional[str] = None
    class_id: Optional[UUID] = None
    class_name: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_classes: int
    assigned_students: int
    created_at: datetime

    class Config:
        from_attributes = True
