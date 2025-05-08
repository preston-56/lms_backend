"""
Diagnostic module for analyzing LMS user activity.
Provides functions to check for issues with the inactive user notification system
and generates easily accessible reports.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from user.models import User
from notification.models import Notification

# Define paths for logs and reports
BASE_DIR = os.path.expanduser("~/lms_backend/diagnostics")
LOG_DIR = os.path.join(BASE_DIR, "lms_logs")
REPORT_DIR = os.path.join(BASE_DIR, "lms_reports")

# Create directories if they don't exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Configure logging to write to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "activity_diagnosis.log"), mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def diagnose_activity(db, inactivity_threshold_days=14):
    """
    Diagnose why inactive users might not be found.
    Returns a summary dict, logs detailed information, and generates a report file.

    Args:
        db: Database session
        inactivity_threshold_days: Number of days after which a user is considered inactive

    Returns:
        Dictionary with diagnostic summary
    """
    timestamp = datetime.utcnow()
    logger.info("Running activity diagnosis")

    # Start with basic user counts
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    inactive_users = db.query(func.count(User.id)).filter(User.is_active == False).scalar()

    # Check for users with missing last_active
    missing_last_active = db.query(func.count(User.id)).filter(User.last_active.is_(None)).scalar()

    # Check for users below the inactivity threshold
    cutoff_date = timestamp - timedelta(days=inactivity_threshold_days)
    potential_inactive = db.query(func.count(User.id))\
                           .filter(User.last_active < cutoff_date)\
                           .filter(User.is_active == True)\
                           .scalar()

    # Sample recent users for last_active distribution
    recent_users = db.query(User)\
                    .filter(User.last_active.isnot(None))\
                    .order_by(User.last_active.desc())\
                    .limit(10)\
                    .all()

    recent_activity = []
    if recent_users:
        for user in recent_users:
            days_since_active = (timestamp - user.last_active).days
            recent_activity.append({
                "user_id": user.id,
                "days_since_active": days_since_active,
                "is_active_flag": user.is_active
            })

    # Sample inactive users that should be notified
    sample_inactive = db.query(User)\
                        .filter(User.last_active < cutoff_date)\
                        .filter(User.is_active == True)\
                        .limit(5)\
                        .all()

    inactive_samples = []
    if sample_inactive:
        logger.info("Sample inactive users that should be notified:")
        for user in sample_inactive:
            days_inactive = (timestamp - user.last_active).days
            has_email = bool(getattr(user, 'email', None))

            inactive_detail = {
                "user_id": user.id,
                "days_inactive": days_inactive,
                "has_email": has_email
            }
            inactive_samples.append(inactive_detail)

            logger.info(f"  User {user.id}: email={has_email}, inactive_days={days_inactive}")
    else:
        logger.info("No inactive users found that meet notification criteria")

    # Check for recent notifications
    one_week_ago = timestamp - timedelta(days=7)
    recent_notifications = db.query(func.count(Notification.id))\
                            .filter(Notification.sent_at >= one_week_ago)\
                            .scalar()

    # Prepare summary
    summary = {
        "timestamp": timestamp.isoformat(),
        "user_counts": {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "users_missing_last_active": missing_last_active,
            "potential_inactive_users": potential_inactive
        },
        "notification_info": {
            "recent_notifications": recent_notifications,
            "threshold_days": inactivity_threshold_days
        },
        "samples": {
            "recent_activity": recent_activity,
            "inactive_samples": inactive_samples
        }
    }

    # Log the summary
    logger.info("Activity diagnosis summary:")
    logger.info(f"  Total users: {total_users}")
    logger.info(f"  Active users: {active_users}")
    logger.info(f"  Users missing last_active: {missing_last_active}")
    logger.info(f"  Potential inactive users: {potential_inactive}")
    logger.info(f"  Recent notifications (7 days): {recent_notifications}")

    # Generate and save the report file
    report_filename = f"activity_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    report_path = os.path.join(REPORT_DIR, report_filename)

    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Also create a human-readable text report
    text_report_filename = f"activity_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
    text_report_path = os.path.join(REPORT_DIR, text_report_filename)

    with open(text_report_path, 'w') as f:
        f.write(f"LMS Activity Diagnosis Report\n")
        f.write(f"Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*50}\n\n")

        f.write(f"USER STATISTICS\n")
        f.write(f"{'-'*20}\n")
        f.write(f"Total users: {total_users}\n")
        f.write(f"Active users: {active_users}\n")
        f.write(f"Inactive users: {inactive_users}\n")
        f.write(f"Users missing last_active: {missing_last_active}\n")
        f.write(f"Potential inactive users: {potential_inactive}\n\n")

        f.write(f"NOTIFICATION SETTINGS\n")
        f.write(f"{'-'*20}\n")
        f.write(f"Inactivity threshold: {inactivity_threshold_days} days\n")
        f.write(f"Recent notifications (7 days): {recent_notifications}\n\n")

        if inactive_samples:
            f.write(f"SAMPLE INACTIVE USERS\n")
            f.write(f"{'-'*20}\n")
            for user in inactive_samples:
                f.write(f"User {user['user_id']}: {user['days_inactive']} days inactive, has email: {user['has_email']}\n")
        else:
            f.write(f"NO INACTIVE USERS FOUND\n")
            f.write(f"{'-'*20}\n")
            f.write(f"No users meet the criteria for inactivity notification.\n")

        if recent_activity:
            f.write(f"\nRECENT USER ACTIVITY\n")
            f.write(f"{'-'*20}\n")
            for user in recent_activity:
                f.write(f"User {user['user_id']}: {user['days_since_active']} days since last active\n")

        f.write(f"\nPOSSIBLE ISSUES\n")
        f.write(f"{'-'*20}\n")
        if total_users == 0:
            f.write(f"- No users found in the database\n")
        if missing_last_active > 0:
            percentage = (missing_last_active / total_users) * 100 if total_users > 0 else 0
            f.write(f"- {missing_last_active} users ({percentage:.1f}%) are missing last_active timestamps\n")
        if potential_inactive == 0 and total_users > 0:
            f.write(f"- No users meet the inactivity threshold of {inactivity_threshold_days} days\n")

    logger.info(f"Diagnosis complete. Reports saved to:")
    logger.info(f"  JSON: {report_path}")
    logger.info(f"  Text: {text_report_path}")

    return {
        "summary": summary,
        "report_paths": {
            "json": report_path,
            "text": text_report_path
        }
    }

def get_latest_report_path():
    """Return the path to the latest activity report"""
    try:
        # Look for text reports
        reports = [f for f in os.listdir(REPORT_DIR) if f.endswith('.txt')]
        if not reports:
            return None

        # Sort by filename (which includes timestamp)
        reports.sort(reverse=True)
        return os.path.join(REPORT_DIR, reports[0])
    except Exception as e:
        logger.error(f"Error finding latest report: {str(e)}")
        return None