"""
Daemon script to notify inactive students in the LMS.

- Connects to the database.
- Uses the notify_inactive_students function to find and email inactive students.
- Includes diagnostic capability to help identify issues.
- Meant to be executed on a schedule (e.g. via systemd timer or cron).
"""

import sys
import os
from database.database import SessionLocal
from email_service.notify import notify_inactive_students
from diagnostics.activity import diagnose_activity

# Check if diagnostics flag is set
ENABLE_DIAGNOSTICS = os.environ.get("LMS_ENABLE_DIAGNOSTICS", "false").lower() == "true"


def run():
    """
    Run the inactive user notification process in a safe DB context.
    """
    db = SessionLocal()
    try:
        # Run the notification process
        count = notify_inactive_students(db)
        print(f"[INFO] Successfully notified {count} inactive user(s).")

        # If diagnostics are enabled or count is 0, run diagnostics
        if ENABLE_DIAGNOSTICS or count == 0:
            print("[INFO] Running activity diagnostics...")
            diagnose_activity(db)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Notification process failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
    # Check for --diagnose flag
    if len(sys.argv) > 1 and sys.argv[1] == "--diagnose":
        print("[INFO] Running in diagnostic mode only...")
        db = SessionLocal()
        try:
            diagnose_activity(db)
        finally:
            db.close()
    else:
        run()
