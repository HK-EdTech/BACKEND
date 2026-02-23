from datetime import datetime
from typing import Optional
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
