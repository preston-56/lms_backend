"""
Course model definition.

This module defines the SQLAlchemy model for courses used in the LMS system.
Each course is associated with an instructor (user) and contains basic
information such as title and description.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    instructor = relationship("User", back_populates="courses")
