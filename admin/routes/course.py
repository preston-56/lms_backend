"""
ADMIN COURSE MANAGEMENT

This module defines the admin-facing endpoints for managing courses within the LMS.
It includes functionality for listing, creating, updating, and deleting courses,
as well as validating instructor assignments.

All endpoints require admin privileges and ensure appropriate role-based validations.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import logging

from database.database import get_db
from models import Course, User
from course.schemas import course as schemas
from auth.utils import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Administrator Course Management"])

@router.get("/courses", response_model=List[schemas.CourseResponse])
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all courses with optional filtering and pagination.
    """
    query = db.query(Course)
    if search:
        query = query.filter(
            (Course.title.ilike(f"%{search}%")) | (Course.description.ilike(f"%{search}%"))
        )
    courses = query.offset(skip).limit(limit).all()
    logger.info(f"Admin {admin.email} listed courses with search={search}")
    return courses


@router.post("/courses", response_model=schemas.CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Create a new course.
    """
    instructor = db.query(User).get(course.instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")
    if instructor.role not in ["admin", "instructor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected user is not an instructor or admin",
        )

    db_course = Course(
        title=course.title,
        description=course.description,
        instructor_id=course.instructor_id,
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    logger.info(f"Admin {admin.email} created course '{course.title}'")
    return db_course


@router.put("/courses/{course_id}", response_model=schemas.CourseResponse)
def update_course(
    course_id: int,
    course_update: schemas.CourseUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Update a course.
    """
    db_course = db.query(Course).get(course_id)
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course_update.title:
        db_course.title = course_update.title
    if course_update.description:
        db_course.description = course_update.description
    if course_update.instructor_id:
        instructor = db.query(User).get(course_update.instructor_id)
        if not instructor:
            raise HTTPException(status_code=404, detail="Instructor not found")
        if instructor.role not in ["admin", "instructor"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected user is not an instructor or admin",
            )
        db_course.instructor_id = course_update.instructor_id

    db.commit()
    db.refresh(db_course)
    logger.info(f"Admin {admin.email} updated course {course_id}")
    return db_course


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Delete a course.
    """
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    logger.info(f"Admin {admin.email} deleted course {course_id}")
    return {"detail": "Course deleted successfully"}
