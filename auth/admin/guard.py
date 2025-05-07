"""
Admin Access Dependency
=======================

This module provides a FastAPI dependency that ensures only users with
an "admin" role can access certain endpoints. It uses the current authenticated
user and checks their role, raising an HTTP 403 error if the user lacks admin privileges.
"""

from fastapi import Depends, HTTPException, status
from auth.utils import get_current_user
from user.models.user import User

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
