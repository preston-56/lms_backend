"""
This module contains Pydantic schemas for handling user-related data.
The schemas are used for validating and structuring data for user creation, updates, and responses.
The `UserRole` Enum defines possible roles for users (e.g., "admin", "instructor", "student").
The schemas include:
- `UserBase`: Shared properties for user-related schemas.
- `UserCreateSchema`: Schema for creating a new user (defaults to 'instructor' role).
- `UserUpdateSchema`: Schema for updating an existing user, allowing for optional updates.
- `UserSchema`: Schema for serializing user data in API responses, including `id`, `role`, and `last_active`.
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

# Enum for User Roles
class UserRole(str, Enum):
    admin = "admin"
    instructor = "instructor"
    student = "student"

# Shared properties for all user-related schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

# Schema for creating a new user (instructor)
class UserCreateSchema(UserBase):
    password: str
    role: Optional[str] = "instructor"

# Schema for updating an existing user (instructor)
class UserUpdateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

# Schema for reading user (instructor) data, used in API responses
class UserSchema(UserBase):
    id: int
    role: str
    last_active: datetime
    is_active: bool

    # Pydantic v2 compatible config
    model_config = ConfigDict(from_attributes=True)
