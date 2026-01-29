from pydantic import BaseModel, Field
from typing import Optional


class ProfileUpdateRequest(BaseModel):
    """Fields that can be updated in base user profile"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Jane",
                "surname": "Smith",
                "username": "janesmith456",
                "avatar_url": "https://example.com/new-avatar.jpg"
            }
        }


class StudentProfileUpdateRequest(BaseModel):
    """Fields that can be updated in student profile"""
    level: Optional[str] = Field(None, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "level": "Form 5"
            }
        }


class TeacherProfileUpdateRequest(BaseModel):
    """Fields that can be updated in teacher profile"""
    bio: Optional[str] = Field(None, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "bio": "I have 10 years of teaching experience in Mathematics."
            }
        }
