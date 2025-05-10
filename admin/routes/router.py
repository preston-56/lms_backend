"""
This module contains the main router for the admin API. It organizes and includes
individual route modules for managing courses, instructors, notifications, and users.

Each route module (e.g., course, instructor, notification, user) is defined in a separate
file and included here to form the complete set of admin routes for the LMS backend.

The routes are grouped by their respective functionality, and the router is then added
to the FastAPI app in the `main.py` file to handle all incoming requests related to
admin operations in the LMS.

Included Routers:
- /courses: Routes for managing courses
- /instructors: Routes for managing instructors
- /notifications: Routes for managing notifications
- /users: Routes for managing users
- /scheduler: Routes for managing scheduler tasks
"""

from fastapi import APIRouter
from .course import router as course_router
from .instructor import router as instructor_router
from .notification import router as notification_router
from .user import router as user_router
from .scheduler import router as scheduler_router

# Create the main router for admin routes
router = APIRouter(prefix="/admin")

# Include individual route modules
router.include_router(course_router)
router.include_router(instructor_router)
router.include_router(notification_router)
router.include_router(scheduler_router)
router.include_router(user_router)
