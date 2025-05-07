"""
This module defines the `Instructor` model for the application.
The `Instructor` model represents the instructors (faculty members) who are part of the system.

Key attributes include:
- `id`: A unique identifier for each instructor.
- `name`: The instructor's full name.
- `email`: The instructor's email address (unique for each instructor).
- `role`: Defines the role of the user (e.g., "admin", "instructor").
- `hashed_password`: Stores the hashed version of the instructor's password for secure authentication.
- `last_active`: A timestamp of the last time the instructor was active in the system.
- `is_active`: A boolean flag indicating whether the instructor's account is active.

Relationships:
- `courses`: Establishes a one-to-many relationship with the `Course` model, linking instructors to the courses they teach.
- `notifications`: Establishes a one-to-many relationship with the `Notification` model, linking instructors to notifications.

The `Instructor` model inherits from `Base`, which is the SQLAlchemy base class for models.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from database.database import Base
from datetime import datetime

class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String)
    hashed_password = Column(String)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    courses = relationship("Course", back_populates="instructor")
    notifications = relationship("Notification", back_populates="user")
