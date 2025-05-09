"""
Student Course Access API
==========================

This module provides endpoints for students or general users to:
- List all available courses
- View details of a specific course

These endpoints do not require admin permissions and are read-only.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from course import schemas, models

router = APIRouter(prefix="/courses", tags=["LMS Student Courses"])

@router.get("/", response_model=list[schemas.CourseResponse])
def list_courses(db: Session = Depends(get_db)):
    """
    List all courses available in the system.
    """
    return db.query(models.Course).all()

@router.get("/{course_id}", response_model=schemas.CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    """
    Retrieve detailed information about a specific course.
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
