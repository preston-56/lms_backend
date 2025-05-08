"""
Admin Scheduler Routes

This module provides admin-only endpoints for interacting with
the scheduler functionality, such as manually triggering scheduled tasks.

All routes in this module require admin privileges to access.
"""

from fastapi import APIRouter, Depends, HTTPException
from auth.utils import require_admin
from schedule import _notify_task_async

router = APIRouter()

@router.post("/run-notifications", dependencies=[Depends(require_admin)])
async def trigger_notifications():
    """
    Manually trigger the notification process.
    Only accessible by admins.
    """
    count = await _notify_task_async()
    return {"status": "success", "message": f"Notification task triggered. Notified {count} inactive students."}