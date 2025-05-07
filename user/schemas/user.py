"""
This module contains Pydantic schemas for the User model.
These schemas are used to define the structure and validation rules for
user-related data, including creating, updating, and retrieving user information.

Schemas:
- UserRole: Enum defining the possible roles for a user.
- UserBase: Shared properties for all user-related schemas.
- UserCreateSchema: Schema for creating a new user, including required fields like password.
- UserUpdateSchema: Schema for updating an existing user with optional fields.
- UserSchema: Schema for reading user data, used in API responses, including fields like `id`, `role`, and `last_active`.

These schemas are designed to ensure data validation and proper handling of user data
throughout the application.
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from enum import Enum
from datetime import datetime

# Enum for User Roles
class UserRole(str, Enum):
    admin = "admin"
    instructor = "instructor"
    student = "student"

# Shared properties for user schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

# Schema for creating a user
class UserCreateSchema(UserBase):
    password: str
    role: Optional[str] = "student"  # Default to "student"

# Schema for updating a user
class UserUpdateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

# Schema for reading user data (API response)
class UserSchema(UserBase):
    id: int
    role: str
    last_active: datetime
    is_active: bool

    # Pydantic v2 config for attribute mapping
    model_config = ConfigDict(from_attributes=True)
