import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.teacher
    school_id: uuid.UUID | None = None
    preferred_language: str = "en"
    country_id: str | None = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = None
    preferred_language: str | None = None
    school_id: uuid.UUID | None = None
    country_id: str | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SchoolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    country_code: str
    district: str | None
    type: str
    connectivity_level: str
    student_count: int
    created_at: datetime
    updated_at: datetime


class SchoolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    country_code: str = Field(min_length=2, max_length=3)
    district: str | None = None
    type: str = "public"
    connectivity_level: str = "medium"
    student_count: int = 0
