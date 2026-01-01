from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class SignupRequest(BaseModel):
    """Profile creation request after Supabase auth"""
    user_id: UUID = Field(..., description="User ID from Supabase auth.users.id")
    first_name: str = Field(..., min_length=1, max_length=100)
    surname: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    role_name: str = Field(..., description="Role name: 'student' or 'teacher' or 'tutorial_teacher'")
    class_level: Optional[str] = Field(None, max_length=50)
    organization_id: Optional[UUID] = Field(None, description="Educational organization ID")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "first_name": "John",
                "surname": "Doe",
                "username": "johndoe123",
                "role_name": "student",
                "class_level": "Form 4",
                "organization_id": None
            }
        }
