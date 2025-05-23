"""
FastAPI LMS Daemon Application

This application serves as the backend for a Learning Management System (LMS).
It includes modules for user management, course content, email services,
admin functionalities, notifications, and authentication.

Features:
- Modular routing using FastAPI's APIRouter
- Database tables auto-created on startup
- OAuth2 password flow for Swagger UI login (Authorize button)
"""

import os
from fastapi import FastAPI, APIRouter
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
import uvicorn
from dotenv import load_dotenv
from database import Base, engine

load_dotenv()

import models

# Routers for different application modules
from admin.routes.router import router as admin_router
from auth.routes import auth_router
from course.routes import course_router
from email_service.routes import email_router
from faculty.routes import instructor_router
from notification.routes import notification_router
from user.routes import user_router
from schedule import lifespan

# Initialize FastAPI app with lifespan manager for handling scheduler
app = FastAPI(lifespan=lifespan)

# Automatically create database tables on app startup
Base.metadata.create_all(bind=engine)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the LMS daemon system"}

# Set up a master API router with a versioned prefix
api_router = APIRouter(prefix="/v1")
"""
 Include all module routers
"""
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(instructor_router)
api_router.include_router(course_router)
api_router.include_router(email_router)
api_router.include_router(notification_router)
api_router.include_router(user_router)

# Register the master router with the app
app.include_router(api_router)

# Setup OAuth2 scheme for Swagger UI login flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

""""
 Custom OpenAPI schema to support OAuth2 password flow in Swagger
"""
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="LMS Daemon API",
        version="1.0.0",
        description="API documentation for the LMS daemon system",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Add security requirement to all routes except auth routes
    for path, path_item in openapi_schema["paths"].items():
        if not path.startswith("/v1/auth/"):
            for method in path_item.values():
                method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Run the FastAPI app using Uvicorn when the script is executed directly
if __name__ == "__main__":
    port = os.environ.get("PORT")
    if not port:
        raise EnvironmentError("PORT environment variable is not set")
    uvicorn.run("fastapi_lms.main:app", host="0.0.0.0", port=int(port), reload=False)