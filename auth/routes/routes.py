"""
Handles authentication and user registration for the application.

Features:
- User registration with role validation.
- Secure admin registration via a protected mechanism.
- Password strength enforcement.
- JWT-based login with secure cookie support.
- Logout route to clear auth cookies.
- Authenticated route to fetch current user profile.

Security Notes:
- Admin registration is only allowed:
    • If it's the first user and the email matches FIRST_ADMIN_EMAIL.
    • Or if a valid admin_key is provided matching ADMIN_REGISTRATION_KEY.
- Any attempt to register with elevated privileges without authorization is logged and downgraded to student role.
- Passwords must meet minimum complexity requirements.

Environment Variables:
- ADMIN_REGISTRATION_KEY: Secret key for admin setup.
- FIRST_ADMIN_EMAIL: Email allowed to register as first admin.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Security
from sqlalchemy.orm import Session
import logging
import os
from typing import Optional

from database import get_db
from models import User
from auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    validate_password_strength
)
from auth.schemas import auth as auth_schemas
from user.schemas import user as schemas

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["User Authentication"])

# Admin registration secret key
ADMIN_REGISTRATION_KEY = os.environ.get("ADMIN_REGISTRATION_KEY", "admin_setup_key")
FIRST_ADMIN_EMAIL = os.environ.get("FIRST_ADMIN_EMAIL")

# ============================================================================
# Registration Endpoint
# ============================================================================

@router.post("/register", response_model=schemas.UserSchema, status_code=status.HTTP_201_CREATED)
def register(
    user: schemas.UserCreateSchema,
    admin_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Register a new user with validation.

    Admin role can only be assigned if:
    - First user and email matches FIRST_ADMIN_EMAIL, or
    - A valid admin_key is provided.

    Unauthorized admin attempts are logged and downgraded to student role.
    """
    # Check if email already exists
    if db.query(User).filter(User.email == user.email).first():
        logger.warning(f"Registration attempt with existing email: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength
    if not validate_password_strength(user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters and include uppercase, lowercase, and numbers"
        )

    # Determine role
    role = "student"  # Default
    is_first_user = db.query(User).count() == 0

    if user.role == "admin" and (
        (is_first_user and FIRST_ADMIN_EMAIL and user.email == FIRST_ADMIN_EMAIL) or
        (admin_key and admin_key == ADMIN_REGISTRATION_KEY)
    ):
        role = "admin"
        logger.info(f"Admin registration for: {user.email}")
    elif user.role != "student":
        logger.warning(f"Attempted registration with role '{user.role}' without proper authorization: {user.email}")
        # Fallback to student role silently

    # Create user
    db_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=role,
        is_active=True,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info(f"New user registered: {user.email} with role: {role}")
    return db_user

# ============================================================================
# Login Endpoint
# ============================================================================

@router.post("/login", response_model=auth_schemas.Token)
def login(response: Response, login: auth_schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    """
    user = db.query(User).filter(User.email == login.email).first()

    if not user or not verify_password(login.password, user.hashed_password):
        logger.warning(f"Failed login attempt for email: {login.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"Login attempt by inactive user: {login.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(user)

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600,
    )

    logger.info(f"User logged in: {login.email}")
    return {"access_token": access_token, "token_type": "bearer"}

# ============================================================================
# Get Current User
# ============================================================================

@router.get("/me", response_model=schemas.UserSchema)
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's information.
    """
    return current_user

# ============================================================================
#  Logout
# ============================================================================

@router.post("/logout")
def logout(response: Response):
    """
    Logout the current user by clearing the auth cookie.
    """
    response.delete_cookie(key="access_token")
    return {"detail": "Successfully logged out"}
