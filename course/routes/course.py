"""
General Course Management API Module
======================================

This module provides endpoints for system-wide course management operations.
These endpoints allow administrators to:
- Create courses with any instructor assignment
- View/list all courses in the system
- Get details of any specific course

Unlike the instructor-specific API, these endpoints don't enforce
instructor-specific permissions and are intended for administrative use.

Endpoints:
- GET /courses/ - List all courses in the system
- GET /courses/{course_id} - Get details of a specific course
- POST /courses/ - Create a new course (instructor must be specified)

"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from course import schemas, models
from user.models import User

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("/", response_model=schemas.CourseResponse)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    # Check if the instructor exists in the users table
    instructor = db.query(User).filter(User.id == course.instructor_id).first()

    if not instructor:
        raise HTTPException(status_code=404, detail="Instructor not found")

    # Proceed with creating the course
    db_course = models.Course(**course.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.get("/{course_id}", response_model=schemas.CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.get("/", response_model=list[schemas.CourseResponse])
def list_courses(db: Session = Depends(get_db)):
    return db.query(models.Course).all()
