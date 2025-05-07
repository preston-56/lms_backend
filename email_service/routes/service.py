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
from datetime import datetime, timedelta

from database.database import get_db
from email_service import schemas, models, utils
from user.models import User

router = APIRouter(prefix="/email", tags=["Email"])

INACTIVITY_DAYS = 7


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
        threshold_date = datetime.utcnow() - timedelta(days=INACTIVITY_DAYS)

        inactive_users = db.query(User).filter(
            User.role == "student",
            User.last_active < threshold_date,
            User.is_active == True
        ).all()

        if not inactive_users:
            return {"message": "No inactive students found."}

        for user in inactive_users:
            user.is_active = False
            db.add(user)

            # Send inactivity email and get the actual body used
            email_body = await utils.send_inactivity_email(email=user.email, name=user.name)

            # Log the sent email
            email_log = models.EmailLog(
                recipient=user.email,
                subject="We've missed you!",
                body=email_body
            )
            db.add(email_log)

        db.commit()
        return {"message": f"Notified {len(inactive_users)} inactive students."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
