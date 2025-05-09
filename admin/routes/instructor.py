"""
Instructor Management Routes for Admins

This module defines API endpoints for managing instructors in the LMS.
All routes are restricted to admin users via the `require_admin` dependency.

Available operations:
- List instructors with optional search and pagination
- Retrieve a specific instructor by ID
- Create a new instructor with enforced role and password validation
- Update instructor details while preserving role integrity
- Soft delete instructors with safety checks (e.g., preventing deletion if assigned to courses)
- Retrieve all courses taught by a given instructor
- Assign an instructor to a course

Each route includes logging for auditing and uses SQLAlchemy ORM for database operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from database.database import get_db
from models import Course, User
from user.schemas.user import UserSchema, UserCreateSchema, UserUpdateSchema
from auth.utils import require_admin, hash_password, validate_password_strength
from course.schemas.course import CourseResponse

router = APIRouter(tags=["Administrator Instructor Management"])
logger = logging.getLogger(__name__)

@router.get("/instructors", response_model=List[UserSchema])
def list_instructors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all instructors with optional filtering and pagination.
    """
    query = db.query(User).filter(User.role == "instructor")
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    instructors = query.offset(skip).limit(limit).all()
    logger.info(f"Admin {admin.email} accessed instructor list")
    return instructors


@router.get("/instructors/{instructor_id}", response_model=UserSchema)
def get_instructor(
    instructor_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get a specific instructor by ID.
    """
    instructor = db.query(User).filter(
        User.id == instructor_id,
        User.role == "instructor"
    ).first()

    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    logger.info(f"Admin {admin.email} accessed instructor {instructor_id}")
    return instructor


@router.post("/instructors", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_instructor(
    instructor: UserCreateSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Create a new instructor.
    """
    if db.query(User).filter(User.email == instructor.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if not validate_password_strength(instructor.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters and include uppercase, lowercase, and numbers",
        )

    db_instructor = User(
        name=instructor.name,
        email=instructor.email,
        hashed_password=hash_password(instructor.password),
        role="instructor",
        is_active=True,
    )
    db.add(db_instructor)
    db.commit()
    db.refresh(db_instructor)
    logger.info(f"Admin {admin.email} created new instructor: {instructor.email}")
    return db_instructor


@router.put("/instructors/{instructor_id}", response_model=UserSchema)
def update_instructor(
    instructor_id: int,
    instructor_update: UserUpdateSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Update an instructor's information.
    """
    db_instructor = db.query(User).filter(
        User.id == instructor_id,
        User.role == "instructor"
    ).first()

    if not db_instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    if instructor_update.name:
        db_instructor.name = instructor_update.name
    if instructor_update.email:
        existing_user = db.query(User).filter(User.email == instructor_update.email).first()
        if existing_user and existing_user.id != instructor_id:
            raise HTTPException(status_code=400, detail="Email already registered")
        db_instructor.email = instructor_update.email
    if instructor_update.password:
        if not validate_password_strength(instructor_update.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters and include uppercase, lowercase, and numbers",
            )
        db_instructor.hashed_password = hash_password(instructor_update.password)
    if instructor_update.is_active is not None:
        db_instructor.is_active = instructor_update.is_active

    if instructor_update.role and instructor_update.role != "instructor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change role through instructor endpoint"
        )

    db.commit()
    db.refresh(db_instructor)
    logger.info(f"Admin {admin.email} updated instructor {instructor_id}")
    return db_instructor


@router.delete("/instructors/{instructor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instructor(
    instructor_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Delete/deactivate an instructor (soft delete).
    """
    if instructor_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    instructor = db.query(User).filter(
        User.id == instructor_id,
        User.role == "instructor"
    ).first()

    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    courses = db.query(Course).filter(Course.instructor_id == instructor_id).all()
    if courses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete instructor with assigned courses. Please reassign courses first."
        )

    instructor.is_active = False
    db.commit()
    logger.info(f"Admin {admin.email} deleted instructor {instructor_id}")
    return {"detail": "Instructor deleted successfully"}


@router.get("/instructors/{instructor_id}/courses", response_model=List[CourseResponse])
def get_instructor_courses(
    instructor_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Get all courses taught by a specific instructor.
    """
    instructor = db.query(User).filter(
        User.id == instructor_id,
        User.role == "instructor"
    ).first()

    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    courses = db.query(Course).filter(Course.instructor_id == instructor_id).all()
    return courses


@router.put("/courses/{course_id}/instructor/{instructor_id}", response_model=CourseResponse)
def assign_instructor_to_course(
    course_id: int,
    instructor_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Assign an instructor to a course.
    """
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    instructor = db.query(User).filter(
        User.id == instructor_id,
        User.role == "instructor",
        User.is_active == True
    ).first()

    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found or inactive")

    course.instructor_id = instructor_id
    db.commit()
    db.refresh(course)

    logger.info(f"Admin {admin.email} assigned instructor {instructor_id} to course {course_id}")
    return course
