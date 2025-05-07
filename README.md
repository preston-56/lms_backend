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

- **Python 3.11+**

* **FastAPI** – Lightweight, async-ready Web API framework
* **SQLAlchemy** – ORM for database modeling
* **Pydantic v2** – Robust data validation and serialization
* **Passlib (bcrypt)** – Secure password hashing
* **Async Email Sender** – Custom utility for background email delivery
* **Modular Structure** – Each domain (e.g.,`user`, `notification`) lives in its own isolated module
* **PostgreSQL** - Database support

---

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
