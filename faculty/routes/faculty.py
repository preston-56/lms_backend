"""
Instructor Course Management API Module
======================================

This module provides endpoints for instructors to manage their courses within the LMS system.
Unlike the admin API which can manage all courses, these endpoints ensure instructors can only:
- Create courses where they are automatically assigned as the instructor
- View/list only courses they teach
- Update only their own courses (and cannot reassign courses to other instructors)
- Delete only their own courses

Each endpoint enforces proper permission checks to maintain data security.
The module implements RESTful CRUD operations with appropriate HTTP methods.

Endpoints:
- GET /instructor/courses/ - List all courses taught by this instructor
- GET /instructor/courses/{course_id} - Get details of a specific course
- POST /instructor/courses/ - Create a new course (instructor auto-assigned)
- PUT /instructor/courses/{course_id} - Update a course's details
- DELETE /instructor/courses/{course_id} - Delete a course

Security:
- All endpoints require authentication
- User must have "instructor" or "admin" role
- Instructors can only access/modify their own courses
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from database import get_db
from models import Course, User
from course.schemas import CourseCreate, CourseResponse, CourseUpdate
from auth.utils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/instructor/courses", tags=["Instructor Course Management"])

# Dependency to check if the user is an instructor or admin
def require_instructor(current_user: User = Depends(get_current_user)):
    """
    Ensures that the current user has the 'instructor' or 'admin' role.
    If the user doesn't have the appropriate role, it raises a Forbidden error.
    """
    if current_user.role not in ["instructor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors can access this endpoint"
        )
    return current_user

@router.get("/", response_model=List[CourseResponse])
def list_instructor_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor)
):
    """
    List all courses taught by the instructor, with optional search and pagination.
    - Only the courses where the instructor is assigned will be returned.
    - Supports search functionality for filtering by course title or description.
    """
    query = db.query(Course).filter(Course.instructor_id == current_user.id)

    if search:
        query = query.filter(
            (Course.title.ilike(f"%{search}%")) |
            (Course.description.ilike(f"%{search}%"))
        )

    courses = query.offset(skip).limit(limit).all()
    return courses

@router.get("/{course_id}", response_model=CourseResponse)
def get_instructor_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor)
):
    """
    Get details of a specific course taught by the instructor.
    - Only the instructor who created the course can view its details.
    """
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.instructor_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or you don't have permission to access it"
        )

    return course

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_instructor_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor)
):
    """
    Create a new course and automatically assign the current instructor as the course instructor.
    - The instructor is automatically set as the course instructor upon creation.
    """
    db_course = Course(
        title=course.title,
        description=course.description,
        instructor_id=current_user.id
    )

    db.add(db_course)
    db.commit()
    db.refresh(db_course)

    logger.info(f"Instructor {current_user.email} created new course: {course.title}")
    return db_course

@router.put("/{course_id}", response_model=CourseResponse)
def update_instructor_course(
    course_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor)
):
    """
    Update an existing course's details.
    - Only the instructor who owns the course can update it.
    """
    db_course = db.query(Course).filter(
        Course.id == course_id,
        Course.instructor_id == current_user.id
    ).first()

    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or you don't have permission to update it"
        )

    if course_update.title:
        db_course.title = course_update.title
    if course_update.description:
        db_course.description = course_update.description

    db.commit()
    db.refresh(db_course)

    logger.info(f"Instructor {current_user.email} updated course {course_id}")
    return db_course

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instructor_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_instructor)
):
    """
    Delete a course from the system.
    - Only the instructor who owns the course can delete it.
    """
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.instructor_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or you don't have permission to delete it"
        )

    db.delete(course)
    db.commit()

    # Log the deletion of the course for auditing purposes
    logger.info(f"Instructor {current_user.email} deleted course {course_id}")
    return {"detail": "Course deleted successfully"}