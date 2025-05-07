"""
Authentication and authorization utilities for the application.

Features:
- Password hashing and strength validation using bcrypt.
- JWT creation and decoding for secure session management.
- OAuth2 password bearer scheme for token-based authentication.
- Role-based access control for admin and instructor-level routes.
- Utility for retrieving the current authenticated user from token.

Security Notes:
- JWT secret is loaded from the `JWT_SECRET_KEY` environment variable, with a fallback for development use.
- JWT tokens expire after 1 hour by default.
- Passwords must be at least 8 characters and include uppercase, lowercase, and numeric characters.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database.database import get_db
from user.models.user import User

# Enhanced security configuration
# Load secret key from environment variable with a fallback for development
SECRET_KEY = (
    os.environ.get("JWT_SECRET_KEY") or "development_secret_do_not_use_in_production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Extended to 1 hour for better UX

# Password settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Password utilities
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength requirements.
    Returns True if password meets requirements, False otherwise.
    """
    # Minimum 8 characters, at least one uppercase, one lowercase, one number
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True


# Token management
def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token for the given user.
    """
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_token_payload(token: str) -> dict:
    """
    Decode and validate a JWT token, returning the payload.
    Raises an HTTPException if validation fails.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from a JWT token.
    """
    payload = get_token_payload(token)
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


# Enhanced role-based access control
def require_role(required_role: str):
    """
    Factory for role-based access control dependencies.
    Example usage: @router.get("/admin", dependencies=[Depends(require_role("admin"))])
    """

    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role.capitalize()} privileges required",
            )
        return current_user

    return role_checker


# Pre-defined role dependencies for common use cases
require_admin = require_role("admin")
require_instructor = require_role("instructor")
