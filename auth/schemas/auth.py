"""
Authentication Schemas
=======================

Defines Pydantic models used for authentication-related operations:

- Token: Schema for returning JWT tokens after login.
- LoginRequest: Schema for validating login input (email and password).
"""

from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
