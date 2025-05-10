#!/usr/bin/env python3
"""
Diagnostic module for analyzing LMS user activity.
Provides functions to check for issues with the inactive user notification system
and generates easily accessible reports.
"""

import os
import json
import logging
import sys
import traceback
from datetime import datetime, timedelta
from sqlalchemy import func

# Define paths for logs and reports
BASE_DIR = os.path.expanduser("~/lms_backend/diagnostics")
LOG_DIR = os.path.join(BASE_DIR, "lms_logs")
REPORT_DIR = os.path.join(BASE_DIR, "lms_reports")

# Create directories if they don't exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Configure logging to write to file only by default
# (Console output can be enabled via command line argument)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# add file handler
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "activity_diagnosis.log"), mode='a')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Add base path to Python module search path
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
logger.info(f"Adding path to Python module search: {base_path}")
sys.path.append(base_path)

# Import models from the central module
try:
    logger.info("Attempting to import models from central module")
    from models import User, Notification
    logger.info("Successfully imported User and Notification models")
except ImportError as e:
    logger.error(f"Failed to import models: {str(e)}")
    logger.error("Make sure the 'models' module is in the Python path")

    # Define placeholder classes if import fails
    class User: pass
    class Notification: pass
    logger.warning("Using placeholder model classes")

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

    # Process recent activity data
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

    # Process inactive user samples
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

    # Generate report files
    timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
    report_files = _generate_reports(timestamp_str, summary, inactive_samples, recent_activity,
                                    total_users, missing_last_active, potential_inactive,
                                    inactivity_threshold_days)

    logger.info(f"Diagnosis complete. Reports saved to:")
    logger.info(f"  JSON: {report_files['json']}")
    logger.info(f"  Text: {report_files['text']}")

    return {
        "summary": summary,
        "report_paths": report_files
    }

def _generate_reports(timestamp_str, summary, inactive_samples, recent_activity,
                     total_users, missing_last_active, potential_inactive,
                     inactivity_threshold_days):
    """Helper function to generate both JSON and text reports"""
    # Generate JSON report
    json_filename = f"activity_report_{timestamp_str}.json"
    json_path = os.path.join(REPORT_DIR, json_filename)
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Generate text report
    text_filename = f"activity_report_{timestamp_str}.txt"
    text_path = os.path.join(REPORT_DIR, text_filename)

    with open(text_path, 'w') as f:
        f.write(f"LMS Activity Diagnosis Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*50}\n\n")

        f.write(f"USER STATISTICS\n")
        f.write(f"{'-'*20}\n")
        f.write(f"Total users: {summary['user_counts']['total_users']}\n")
        f.write(f"Active users: {summary['user_counts']['active_users']}\n")
        f.write(f"Inactive users: {summary['user_counts']['inactive_users']}\n")
        f.write(f"Users missing last_active: {summary['user_counts']['users_missing_last_active']}\n")
        f.write(f"Potential inactive users: {summary['user_counts']['potential_inactive_users']}\n\n")

        f.write(f"NOTIFICATION SETTINGS\n")
        f.write(f"{'-'*20}\n")
        f.write(f"Inactivity threshold: {summary['notification_info']['threshold_days']} days\n")
        f.write(f"Recent notifications (7 days): {summary['notification_info']['recent_notifications']}\n\n")

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

    return {
        "json": json_path,
        "text": text_path
    }

def get_latest_report_path():
    """Return the path to the latest activity report"""
    try:
        reports = [f for f in os.listdir(REPORT_DIR) if f.endswith('.txt')]
        if not reports:
            return None

        # Sort by filename (which includes timestamp)
        reports.sort(reverse=True)
        return os.path.join(REPORT_DIR, reports[0])
    except Exception as e:
        logger.error(f"Error finding latest report: {str(e)}")
        return None

def get_database_session():
    """Get a database session using the most appropriate method"""
    # Try to import directly from the database module
    try:
        logger.info("Importing database session from database module")
        from database import SessionLocal
        db = SessionLocal()
        logger.info("Successfully created database session")
        return db
    except (ImportError, AttributeError) as e:
        logger.warning(f"Direct database import failed: {str(e)}")

    # Try to get database URL from environment and create a session
    try:
        logger.info("Creating database session from DATABASE_URL")
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from dotenv import load_dotenv

        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL")

        if not DATABASE_URL:
            logger.warning("DATABASE_URL environment variable not found")
            return None

        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()
        logger.info("Successfully created database session from URL")
        return db
    except Exception as e:
        logger.warning(f"Failed to create session from DATABASE_URL: {str(e)}")

    return None

def main():
    """Run the diagnostic tool with proper argument handling"""
    import argparse

    parser = argparse.ArgumentParser(description='LMS User Activity Diagnostic Tool')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print diagnostic information to console')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress all console output')
    parser.add_argument('--days', '-d', type=int, default=14,
                        help='Inactivity threshold in days (default: 14)')
    parser.add_argument('--output', '-o', choices=['path', 'none'], default='path',
                        help='What to output to console (default: report path)')

    args = parser.parse_args()

    # Add console handler if verbose mode is enabled
    if args.verbose and not args.quiet:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

    try:
        # Get database session
        db = get_database_session()

        if db is None:
            logger.error("Could not establish database connection")
            if not args.quiet:
                sys.stderr.write("\nDATABASE CONNECTION ERROR\n")
                sys.stderr.write("-"*30 + "\n")
                sys.stderr.write("Could not establish a database connection.\n\n")
                sys.stderr.write("Troubleshooting steps:\n")
                sys.stderr.write("1. Make sure your virtual environment is activated\n")
                sys.stderr.write("2. Run this script from the project root directory\n")
                sys.stderr.write("3. Set the DATABASE_URL environment variable\n")
            return 1

        # Run the diagnosis
        logger.info(f"Starting activity diagnosis with threshold of {args.days} days")
        result = diagnose_activity(db, inactivity_threshold_days=args.days)

        # Only output to console if not in quiet mode
        if not args.quiet and args.output == 'path':
            latest_report = get_latest_report_path()
            if latest_report:
                sys.stdout.write(f"{latest_report}\n")

        return 0

    except Exception as e:
        logger.error(f"Error running diagnostics: {str(e)}")
        logger.error(traceback.format_exc())
        if not args.quiet:
            sys.stderr.write(f"Error running diagnostics: {str(e)}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())