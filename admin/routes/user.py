"""
Admin routes for managing users in the LMS system.

These endpoints allow admin users to:
- List users with filters
- Retrieve specific user data
- Create new users
- Update existing user details
- Soft-delete users

Access is restricted to admin users via `require_admin`.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from database import get_db
from models import User
from user.schemas.user import UserSchema, UserCreateSchema, UserUpdateSchema
from auth.utils import require_admin, hash_password, validate_password_strength

router = APIRouter(prefix="/users", tags=["Administrator User Management"])
logger = logging.getLogger(__name__)

@router.get("/users", response_model=List[UserSchema])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all users with optional filtering by name/email and role.

    - **skip**: Number of records to skip (pagination).
    - **limit**: Maximum number of records to return.
    - **search**: Case-insensitive partial match on name or email.
    - **role**: Filter by user role (e.g. 'admin', 'student').
    """
    query = db.query(User)
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    if role:
        query = query.filter(User.role == role)
    users = query.offset(skip).limit(limit).all()
    logger.info(f"Admin {admin.email} accessed user list")
    return users


@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get a specific user by ID.
    """
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"Admin {admin.email} accessed user {user_id}")
    return user


@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreateSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Create a new user.

    Validates:
    - Email uniqueness
    - Password strength
    """
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if not validate_password_strength(user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters and include uppercase, lowercase, and numbers",
        )

    db_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role or "student",
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"Admin {admin.email} created new user: {user.email}")
    return db_user


@router.put("/users/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int,
    user_update: UserUpdateSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Update a user's information.

    Supports updating:
    - Name
    - Email (ensures uniqueness)
    - Password (validates strength)
    - Role
    - Active status
    """
    db_user = db.query(User).get(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.name:
        db_user.name = user_update.name
    if user_update.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")
        db_user.email = user_update.email
    if user_update.password:
        if not validate_password_strength(user_update.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters and include uppercase, lowercase, and numbers",
            )
        db_user.hashed_password = hash_password(user_update.password)
    if user_update.role:
        db_user.role = user_update.role
    if user_update.is_active is not None:
        db_user.is_active = user_update.is_active

    db.commit()
    db.refresh(db_user)
    logger.info(f"Admin {admin.email} updated user {user_id}")
    return db_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Soft delete a user by marking them as inactive.

    Prevents deletion of the currently authenticated admin.
    """
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    logger.info(f"Admin {admin.email} deleted user {user_id}")
    return {"detail": "User deleted successfully"}
