"""
FastAPI Scheduler Integration

This module provides integration between FastAPI and APScheduler
to run background tasks like the daemon functionality.
It includes:
- Background scheduler configuration
- Lifecycle management (start/stop with application)
- Scheduled tasks for notifications and diagnostics
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
import logging
import asyncio
import os

# Import existing daemon functions
from database import SessionLocal
from email_service.notify import notify_inactive_students
from diagnostics.activity import diagnose_activity

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a scheduler instance
scheduler = BackgroundScheduler()

def notify_task_wrapper():
    """Non-async wrapper for the async notify_task function"""
    logger.info("Running scheduled notification task")
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Run the async function using the event loop
        return loop.run_until_complete(_notify_task_async())
    finally:
        loop.close()

async def _notify_task_async():
    """Async implementation of the notification task"""
    db = SessionLocal()
    try:
        # Run the notification process
        count = await notify_inactive_students(db)
        logger.info(f"Successfully notified {count} inactive user(s).")

        # Run diagnostics if needed
        enable_diagnostics = os.environ.get("LMS_ENABLE_DIAGNOSTICS", "false").lower() == "true"
        if enable_diagnostics or count == 0:
            logger.info("Running activity diagnostics...")
            diagnose_activity(db)

        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Notification process failed: {e}")
        return 0
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app):
    """
    FastAPI lifespan event handler to start and stop the scheduler
    with the application lifecycle.
    """
    # Only start scheduler if not in testing mode
    if os.environ.get("ENVIRONMENT") != "testing":
        # Get the cron schedule from environment variable or use default
        cron_schedule = os.environ.get("NOTIFICATION_SCHEDULE", "0 8 * * *")

        # Parse the cron expression into components
        try:
            minute, hour, day, month, day_of_week = cron_schedule.split()
        except ValueError:
            logger.warning(f"Invalid cron expression: {cron_schedule}. Using default (8 AM daily).")
            minute, hour, day, month, day_of_week = "0", "8", "*", "*", "*"

        # Start the scheduler
        logger.info("Starting scheduler")
        scheduler.start()

        # Add the job - using the parsed cron components
        scheduler.add_job(
            notify_task_wrapper,  # Use the non-async wrapper
            CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            ),
            id="notify_inactive_students",
            name="Notify inactive students according to schedule",
            replace_existing=True,
        )
        logger.info(f"Scheduled task: notify_inactive_students with schedule: {cron_schedule}")

    yield

    # Shutdown the scheduler when the app stops
    if os.environ.get("ENVIRONMENT") != "testing" and scheduler.running:
        logger.info("Shutting down scheduler")
        scheduler.shutdown()