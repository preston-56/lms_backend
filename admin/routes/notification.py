
"""
NOTIFICATION MANAGEMENT

This module defines the admin-facing endpoints for managing notifications within the LMS.
It includes functionality for listing notifications and sending new notifications to all users.

All endpoints require admin privileges to ensure appropriate role-based validations.
"""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
import logging

from database import get_db
from models import User, Notification
from notification.schemas import notification as schemas
from auth.utils import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Administrator Notification Management"])

@router.get("/notifications", response_model=List[schemas.NotificationResponse])
def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    List all notifications.
    """
    notifications = db.query(Notification).offset(skip).limit(limit).all()
    return notifications


@router.post("/notifications", response_model=schemas.NotificationResponse, status_code=status.HTTP_201_CREATED)
def send_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Send a new notification to all users.
    """
    new_notification = Notification(
        message=notification.message,
        user_id=admin.id
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    logger.info(f"Admin {admin.email} sent notification: {notification.message[:50]}...")
    return new_notification

