"""
Email notification routes for the LMS application.

This module defines API endpoints for:
- Sending general emails and logging them to the database.
- Notifying inactive students and marking them as inactive.

Dependencies:
- FastAPI for routing and dependency injection.
- SQLAlchemy for database session handling.
- Custom utilities for email sending logic.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from email_service import schemas, models, utils
from email_service.notify import notify_inactive_users

router = APIRouter(prefix="/email", tags=["Email"])


@router.post("/", response_model=schemas.EmailLogResponse)
async def send_email_route(email: schemas.EmailRequest, db: Session = Depends(get_db)):
    """
    Send a general email to a specified recipient and log it in the database.
    """
    try:
        await utils.send_email(email.recipient, email.subject, email.body)

        email_log = models.EmailLog(
            recipient=email.recipient,
            subject=email.subject,
            body=email.body
        )
        db.add(email_log)
        db.commit()
        db.refresh(email_log)
        return email_log

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inactive/")
async def notify_inactive_students(db: Session = Depends(get_db)):
    """
    Find inactive students and send them a reminder email.
    """
    try:
        count = notify_inactive_users(db)
        return {"message": f"Notified {count} inactive students."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
