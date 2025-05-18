"""
Module for handling notifications to inactive students in the LMS.

This module contains functions to:
- Identify inactive students based on last activity timestamp
- Send notification emails to those students
- Update their status in the database
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import User, Notification
from email_service.utils import send_email

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration - you can modify these values based on your requirements
INACTIVITY_THRESHOLD_DAYS = 14  # Students are considered inactive after 14 days
NOTIFICATION_EMAIL_SUBJECT = "We miss you in your online courses!"


async def notify_inactive_students(db: Session) -> int:
    """
    Find inactive students, send them notification emails, and mark them as notified.

    Args:
        db: The database session

    Returns:
        The number of students notified

    Raises:
        Exception: If there's an error in the notification process
    """
    # Log the start of the process and configuration
    logger.info(f"Starting inactive student notification process")
    logger.info(f"Inactivity threshold set to {INACTIVITY_THRESHOLD_DAYS} days")

    # Get total number of users for diagnostic purposes
    total_users_count = db.query(func.count(User.id)).scalar()
    logger.info(f"Total users in database: {total_users_count}")

    # Calculate the cutoff date for inactivity
    cutoff_date = datetime.utcnow() - timedelta(days=INACTIVITY_THRESHOLD_DAYS)
    logger.info(f"Inactivity cutoff date: {cutoff_date}")

    # Count total users with last_active data
    users_with_last_active = (
        db.query(func.count(User.id)).filter(User.last_active.isnot(None)).scalar()
    )
    logger.info(f"Users with last_active data: {users_with_last_active}")

    # Query for inactive users
    inactive_users = (
        db.query(User)
        .filter(User.last_active < cutoff_date)
        .filter(User.is_active == True)
        .all()
    )

    logger.info(f"Found {len(inactive_users)} inactive users")

    # If no inactive users, return early
    if not inactive_users:
        logger.info("No inactive users found that need notification")
        return 0

    # For each inactive user
    notification_count = 0
    for user in inactive_users:
        logger.info(
            f"Processing user ID {user.id}, email: {user.email}, last active: {user.last_active}"
        )

        try:
            # Create notification message
            message = f"""
Hello {user.name},

We've noticed that you haven't been active in your courses for a while.
Your last activity was on {user.last_active.strftime('%Y-%m-%d')}.

Please log in to continue your learning journey!

Best regards,
The LMS Team
            """

            # Send email
            logger.info(f"Sending notification email to {user.email}")
            await send_email(user.email, NOTIFICATION_EMAIL_SUBJECT, message)

            # Create notification record in DB
            notification = Notification(
                user_id=user.id,
                message=f"Inactivity notification sent on {datetime.utcnow().strftime('%Y-%m-%d')}",
            )
            db.add(notification)

            # Update user's notification timestamp
            user.last_notification = datetime.utcnow()

            notification_count += 1
            logger.info(f"Successfully notified user {user.id}")

        except Exception as e:
            logger.error(f"Error notifying user {user.id}: {str(e)}")
            # Don't re-raise to continue processing other users
            # However, if an error occurs consistently, it will show up in logs

    # Commit all changes at once
    if notification_count > 0:
        logger.info(f"Committing changes to database for {notification_count} users")
        db.commit()

    logger.info(f"Notification process complete. Notified {notification_count} users.")
    return notification_count


def get_inactive_users_report(db: Session):
    """
    Generate a diagnostic report of user activity status.
    This can be useful for manually checking the state of user activity.

    Args:
        db: The database session

    Returns:
        A dictionary with various metrics about user activity
    """
    total_users = db.query(func.count(User.id)).scalar()

    # Get counts for various statuses
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()

    inactive_users = (
        db.query(func.count(User.id)).filter(User.is_active == False).scalar()
    )

    # Users without last_active data
    no_last_active = (
        db.query(func.count(User.id)).filter(User.last_active.is_(None)).scalar()
    )

    # Users potentially needing notification (inactive for threshold period but not yet marked inactive)
    cutoff_date = datetime.utcnow() - timedelta(days=INACTIVITY_THRESHOLD_DAYS)
    need_notification = (
        db.query(func.count(User.id))
        .filter(User.last_active < cutoff_date)
        .filter(User.is_active == True)
        .scalar()
    )

    # Recent activity (last 7 days)
    recent_activity_date = datetime.utcnow() - timedelta(days=7)
    recent_activity = (
        db.query(func.count(User.id))
        .filter(User.last_active >= recent_activity_date)
        .scalar()
    )

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "users_without_last_active": no_last_active,
        "users_needing_notification": need_notification,
        "users_with_recent_activity": recent_activity,
        "inactivity_threshold_days": INACTIVITY_THRESHOLD_DAYS,
        "report_generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }
