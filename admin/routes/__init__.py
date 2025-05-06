"""
Admin routes package initializer.

This module initializes and exposes the main routes for the admin functionalities
in the Learning Management System (LMS).
"""

# Import individual route modules
from .course import router as course_router
from .instructor import router as instructor_router
from .notification import router as notification_router
from .user import router as user_router

# Aggregate all the routers into a single list for easy inclusion in the main app
routers = [
    course_router,
    instructor_router,
    notification_router,
    user_router,
]

# Expose the routers and individual route handlers for external use
__all__ = [
    "routers",
    "course_router",
    "instructor_router",
    "notification_router",
    "user_router"
]
