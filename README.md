# LMS Daemon Backend

**LMS Daemon Backend** is a modular backend system for a Learning Management System built with FastAPI. It supports core LMS operations like user management, course delivery, notifications, and admin tasks. The system is designed with a daemon-style architecture to handle background processes such as inactivity checks and email alerts automatically.

---

### Features

- **User Management**
  Create, update, list, and delete users with role-based distinctions: `admin`, `instructor`, and `student`.
- **Course & Notification Modules**
  Manage courses and send notifications to specific users. Each notification includes a message and timestamp.
- **Email Service**
  Send custom emails and auto-notify inactive students based on their `last_active` timestamp.
- **Background Daemon Support**
  Continuously monitor student activity and automatically send email reminders to inactive students, reducing manual oversight and ensuring timely engagement interventions.

---

### Daemon Automation

Rather than relying on manual scripts, the system runs background tasks automatically. It continuously:

* Scans for inactive students
* Sends scheduled or rule-based emails
* Logs email activity for auditing

This approach ensures the system runs autonomously and is ready for production use.

---

### Tech Stack

* **Python 3.11+**
* **FastAPI** – Lightweight, async-ready Web API framework
* **SQLAlchemy** – ORM for database modeling
* **Pydantic v2** – Robust data validation and serialization
* **Passlib (bcrypt)** – Secure password hashing
* **Async Email Sender** – Custom utility for background email delivery
* **Modular Structure** – Each domain (e.g.,`user`, `notification`) lives in its own isolated module
* **PostgreSQL** - Database support

---

### Folder Structure

```bash
    lms_backend/
    ├── admin/                                  # Admin module for system administration
    │   ├── __init__.py
    │   ├── guard.py                            # Security guard for admin operations
    │   └── routes/                             # Admin API endpoints
    │       ├── __init__.py
    │       ├── course.py                       # Course administration routes
    │       ├── instructor.py                   # Instructor management routes
    │       ├── notification.py                 # Notification management routes
    │       ├── router.py                       # Main admin router configuration
    │       └── user.py                         # User administration routes
    │
    ├── auth/                                   # Authentication and authorization module
    │   ├── __init__.py
    │   ├── admin/                              # Admin-specific authentication
    │   │   ├── __init__.py
    │   │   └── guard.py                        # Admin authentication guard
    │   ├── routes/                             # Auth API endpoints
    │   │   ├── __init__.py
    │   │   └── routes.py                       # Authentication routes (login, register, etc.)
    │   ├── schemas/                            # Auth data validation schemas
    │   │   ├── __init__.py
    │   │   └── auth.py                         # Authentication schemas
    │   └── utils.py                            # Auth utility functions
    │
    ├── course/                                 # Course management module
    │   ├── __init__.py
    │   ├── models/                             # Course data models
    │   │   ├── __init__.py
    │   │   └── course.py                       # Course database model
    │   ├── routes/                             # Course API endpoints
    │   │   ├── __init__.py
    │   │   └── course.py                       # Course CRUD operations
    │   └── schemas/                            # Course data validation schemas
    │       ├── __init__.py
    │       └── course.py                       # Course request/response schemas
    │
    ├── daemon/                                 # Background processing service
    │   ├── __init__.py
    │   └── daemon.py                           # Main daemon script for scheduled tasks and background jobs
    │
    ├── database/                               # Database connection management
    │   ├── __init__.py                         # Exports get_db function
    │   └── database.py                         # Database connection configuration
    │
    ├── diagnostics/                            # System diagnostics and monitoring
    │   ├── __init__.py
    │   ├── activity.py                         # User activity diagnostics
    │   ├── view_reports.py                     # Report viewing utilities
    │   ├── lms_logs/                           # Diagnostic logs directory
    │   │   └── activity_diagnosis.log          # Activity diagnostic logs
    │   └── lms_reports/                        # Generated reports directory
    │       └── activity_report_*.json/txt      # Activity reports in JSON/TXT format
    │
    ├── email_service/                          # Email notification service
    │   ├── __init__.py
    │   ├── notify.py                           # Email notification functions
    │   ├── utils.py                            # Email utility functions
    │   ├── models/                             # Email service models
    │   │   ├── __init__.py
    │   │   └── service.py                      # Email service data model
    │   ├── routes/                             # Email service API endpoints
    │   │   ├── __init__.py
    │   │   └── service.py                      # Email service routes
    │   └── schemas/                            # Email service data validation
    │       ├── __init__.py
    │       └── service.py                      # Email schemas
    │
    ├── faculty/                                # Faculty management module
    │   ├── __init__.py
    │   ├── models/                             # Faculty data models
    │   │   ├── __init__.py
    │   │   └── faculty.py                      # Faculty database model
    │   ├── routes/                             # Faculty API endpoints
    │   │   ├── __init__.py
    │   │   └── faculty.py                      # Faculty CRUD operations
    │   └── schemas/                            # Faculty data validation schemas
    │       ├── __init__.py
    │       └── faculty.py                      # Faculty request/response schemas
    │
    ├── fastapi_lms/                            # FastAPI application integration
    │   └── main.py                             # FastAPI main application with modular routing
    │
    ├── lms/                                    # MAIN APPLICATION CORE (Django Project)
    │   ├── __init__.py
    │   ├── asgi.py                             # ASGI configuration for async web servers
    │   ├── settings.py                         # Core Django project settings
    │   ├── urls.py                             # Main URL routing configuration
    │   └── wsgi.py                             # WSGI configuration for web servers
    │
    ├── models/                                 # Centralized model imports
    │   └── __init__.py                         # Imports and exports models for cleaner imports
    │
    ├── notification/                           # Notification system module
    │   ├── __init__.py
    │   ├── models/                             # Notification data models
    │   │   ├── __init__.py
    │   │   └── notification.py                 # Notification database model
    │   ├── routes/                             # Notification API endpoints
    │   │   ├── __init__.py
    │   │   └── notification.py                 # Notification CRUD and sending operations
    │   └── schemas/                            # Notification data validation schemas
    │       ├── __init__.py
    │       └── notification.py                 # Notification request/response schemas
    │
    ├── user/                                   # User management module
    │   ├── utils.py                            # User-specific utility functions
    │   ├── models/                             # User data models
    │   │   ├── __init__.py
    │   │   └── user.py                         # User database model
    │   ├── routes/                             # User API endpoints
    │   │   ├── __init__.py
    │   │   └── user.py                         # User CRUD operations
    │   └── schemas/                            # User data validation schemas
    │       ├── __init__.py
    │       └── user.py                         # User request/response schemas
    │
    ├── .gitignore                              # Git ignore configuration
    ├── README.md                               # Project documentation
    ├── manage.py                               # Django management script
    └── requirements.txt                        # Python dependencies
```

### Setup & Installation

1. **Clone the repository:**

   ```bash
      git@github.com:preston-56/lms_backend.git

      cd lms-backend
   ```
2. **Create a virtual environment:**

   ```bash
      python3 -m venv venv
      source venv/bin/activate # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**

   ```bash
     pip install -r requirements.txt

   ```
4. **Run the app:**

   ```bash
      uvicorn fastapi_lms.main:app --reload
   ```

- Visit `http://127.0.0.1:8000/docs` for Swagger UI.

---

### Authentication Flow

* Uses OAuth2 with Password (JWT) flow.
* Authenticate via the `/v1/auth/login` endpoint.
* Click “Authorize” in Swagger UI to use secured routes.

---

### API Documentation

Auto-generated via FastAPI and available at:

* [Swagger UI](http://localhost:8000/docs)
* [ReDoc](http://localhost:8000/redoc)
