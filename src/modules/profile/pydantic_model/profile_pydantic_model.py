from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class StudentProfileResponse(BaseModel):
    """Student-specific profile information"""
    id: UUID
    level: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeacherProfileResponse(BaseModel):
    """Teacher-specific profile information"""
    id: UUID
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    """Matches Supabase public.profiles table"""
    id: UUID
    first_name: str
    surname: str
    full_name: Optional[str] = Field(None, description="Auto-generated from first_name + surname")
    username: str
    role_name: Optional[str] = Field(None, description="User role: 'student', 'teacher', or 'private_tutor'")
    organization_id: Optional[UUID] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Role-specific profiles
    student_profile: Optional[StudentProfileResponse] = None
    teacher_profile: Optional[TeacherProfileResponse] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "first_name": "John",
                "surname": "Doe",
                "full_name": "John Doe",
                "username": "johndoe123",
                "role_name": "student",
                "organization_id": None,
                "avatar_url": "https://example.com/avatar.jpg",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "student_profile": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "level": "Form 4",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                "teacher_profile": None
            }
        }
