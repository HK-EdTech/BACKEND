from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class HomeworkResponse(BaseModel):
    id: str
    title: Optional[str] = None
    subject: Optional[str] = None
    class_id: Optional[str] = None
    due_date: Optional[datetime] = None
    full_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ClassWithHomeworkResponse(BaseModel):
    id: str
    name: str
    subject: str
    target_level: Optional[str] = None
    organization_id: Optional[str] = None
    created_at: datetime
    homework: List[HomeworkResponse] = []

    class Config:
        from_attributes = True
