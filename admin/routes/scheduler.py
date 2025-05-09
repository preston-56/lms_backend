"""
Admin Scheduler Routes

This module provides admin-only endpoints for interacting with
the scheduler functionality, such as manually triggering scheduled tasks.

All routes in this module require admin privileges to access.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from auth.utils import require_admin
from schedule import _notify_task_async, scheduler
from apscheduler.triggers.cron import CronTrigger
import os

router = APIRouter(prefix="/scheduler", tags=["Administrator  Schedule Management"])

@router.post("/run-notifications")
async def trigger_notifications(admin=Depends(require_admin)):
    """
    Manually trigger the notification process.
    Only accessible by admins.
    """
    count = await _notify_task_async()
    return {
        "status": "success",
        "message": f"Notification task triggered. Notified {count} inactive students."
    }

@router.get("/status")
async def get_scheduler_status(admin=Depends(require_admin)):
    """
    Get the status of the scheduler and its jobs.
    Only accessible by admins.
    """
    if not scheduler.running:
        return {"status": "stopped", "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": jobs,
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "diagnostics_enabled": os.environ.get("LMS_ENABLE_DIAGNOSTICS", "false").lower() == "true"
    }

@router.post("/{action}")
async def control_scheduler(
    action: str,
    admin=Depends(require_admin)
):
    """
    Control the scheduler (pause, resume, restart).
    Only accessible by admins.

    Valid actions:
    - pause: Pause the scheduler
    - resume: Resume the scheduler
    - restart: Restart the scheduler
    """
    if action == "pause":
        if scheduler.running:
            scheduler.pause()
            return {"status": "success", "message": "Scheduler paused"}
        return {"status": "error", "message": "Scheduler is not running"}

    elif action == "resume":
        if scheduler.state == 1:  # STATE_PAUSED
            scheduler.resume()
            return {"status": "success", "message": "Scheduler resumed"}
        return {"status": "error", "message": "Scheduler is not paused"}

    elif action == "restart":
        if scheduler.running:
            scheduler.shutdown()
        scheduler.start()
        # Re-add the job with the current schedule
        cron_schedule = os.environ.get("NOTIFICATION_SCHEDULE", "0 8 * * *")
        try:
            minute, hour, day, month, day_of_week = cron_schedule.split()
        except ValueError:
            minute, hour, day, month, day_of_week = "0", "8", "*", "*", "*"

        from schedule import notify_task_wrapper
        scheduler.add_job(
            notify_task_wrapper,
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
        return {"status": "success", "message": "Scheduler restarted"}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}. Valid actions are: pause, resume, restart"
        )