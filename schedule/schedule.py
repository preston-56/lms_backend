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

# Import existing daemon functions
from database.database import SessionLocal
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
        if count == 0:
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
    # Start the scheduler
    logger.info("Starting scheduler")
    scheduler.start()

    # Add the job - run at 8:00 AM every day
    scheduler.add_job(
        notify_task_wrapper,  # Use the non-async wrapper
        CronTrigger(hour=8, minute=0),
        id="notify_inactive_students",
        name="Notify inactive students daily",
        replace_existing=True,
    )
    logger.info("Scheduled task: notify_inactive_students")

    yield

    # Shutdown the scheduler when the app stops
    logger.info("Shutting down scheduler")
    scheduler.shutdown()