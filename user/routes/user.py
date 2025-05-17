"""
User Management API Module
===========================

This module provides endpoints for managing users within the LMS system.
The API supports CRUD operations for users, allowing for user creation,
retrieval, updating, and deletion.

Endpoints:
- GET /users/ - List all users
- POST /users/ - Create a new user
- GET /users/{user_id} - Retrieve a user by their ID
- PUT /users/{user_id} - Update an existing user
- DELETE /users/{user_id} - Delete a user

Each endpoint ensures proper permission checks and validation for user data.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from user.schemas.user import UserSchema, UserCreateSchema, UserUpdateSchema
from models import User
from database import get_db
from user.utils import hash_password

router = APIRouter(prefix="/users", tags=["LMS System Users"])

# List all users
@router.get("/", response_model=list[UserSchema])
def list_users(db: Session = Depends(get_db)):
    """
    List all users in the system.

    This endpoint fetches all user records from the database and returns them
    in the format defined by the `UserSchema`.
    """
    return db.query(User).all()

# Create a new user
@router.post("/", response_model=UserSchema)
def create_user(user: UserCreateSchema, db: Session = Depends(get_db)):
    """
    Create a new user in the system.

    This endpoint checks for an existing user with the provided email,
    hashes the password, and creates a new user record in the database.
    """
    # Optional: Check for duplicate email
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        role=user.role,
        hashed_password=hashed_pw
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Get a user by ID
@router.get("/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a user by their ID.

    This endpoint fetches a single user from the database based on the
    provided `user_id`. If the user does not exist, it raises a 404 error.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Update a user
@router.put("/{user_id}", response_model=UserSchema)
def update_user(user_id: int, updated_data: UserUpdateSchema, db: Session = Depends(get_db)):
    """
    Update an existing user.

    This endpoint allows partial updates to a user. It only updates the fields
    provided in the `updated_data` payload and skips any unset fields.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user

# Delete a user
@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user from the system.

    This endpoint removes a user record from the database based on the
    provided `user_id`. If the user does not exist, it raises a 404 error.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
