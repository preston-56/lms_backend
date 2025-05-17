"""
This module defines the SQLAlchemy User model for the application.
The model represents a user in the system and includes fields for the user's
name, email, role, password, activity status, and relationships with
notifications.

Fields:
- id: Unique identifier for the user.
- name: Name of the user.
- email: Email address of the user (must be unique).
- role: Role of the user (e.g., "admin", "instructor", or "student").
- hashed_password: Hashed password for authentication.
- last_active: The last time the user was active.
- is_active: Whether the user is active or not (default is True).

Relationships:
- notifications: Relationship with the Notification model, representing notifications for the user.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String)  # "admin", "instructor" or "student"
    hashed_password = Column(String)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    notifications = relationship("Notification", back_populates="user")