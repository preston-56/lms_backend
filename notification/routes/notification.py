"""
Notification API Module
=======================

This module provides endpoints for managing user notifications within the LMS.

Features:
- Send a notification to a user
- Retrieve all notifications

Endpoints:
- POST /notifications/ : Create and send a notification to a specific user
- GET /notifications/ : Retrieve all notifications stored in the system

Security:
- Currently unauthenticated; can be extended with role checks and token verification

Each notification includes:
- `user_id`: Target user receiving the notification
- `message`: Notification content
- `sent_at`: Timestamp when the notification was created
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from notification import models, schemas
from models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/", response_model=schemas.NotificationResponse, status_code=status.HTTP_201_CREATED)
def send_notification(notification: schemas.NotificationCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.id == notification.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create and save the notification
    db_notification = models.Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.get("/", response_model=list[schemas.NotificationResponse])
def get_all_notifications(db: Session = Depends(get_db)):
    # Return all notifications
    return db.query(models.Notification).all()
