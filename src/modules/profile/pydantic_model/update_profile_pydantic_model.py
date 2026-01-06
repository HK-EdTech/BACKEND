from pydantic import BaseModel, Field
from typing import Optional


class ProfileUpdateRequest(BaseModel):
    """Fields that can be updated in user profile"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    class_level: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Jane",
                "surname": "Smith",
                "username": "janesmith456",
                "class_level": "Form 5",
                "avatar_url": "https://example.com/new-avatar.jpg"
            }
        }
