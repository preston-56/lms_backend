"""
Email service for sending notifications using FastMail.

- Configures the email connection using environment variables.
- Initializes FastMail instance to avoid repeated setup.
- Provides two functions for sending emails:
  - `send_email`: General-purpose email sender.
  - `send_inactivity_email`: Specific email sender for inactivity reminders.
  - `send_inactivity_email_sync`: Sync wrapper for daemon scripts.

Environment Variables:
- MAIL_USERNAME: Email username for authentication.
- MAIL_PASSWORD: Email password for authentication.
- MAIL_FROM: Email address to send emails from.
- MAIL_FROM_NAME: Display name for the sender in email.
"""

import os
import asyncio
from dotenv import load_dotenv
from pydantic import EmailStr
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

load_dotenv()

# Email configuration using environment variables
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="LMS Notifications",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

# Initialize FastMail once to avoid repeated instantiation
fm = FastMail(conf)


# General-purpose email sender
async def send_email(recipient: EmailStr, subject: str, body: str):
    """
    Send a general email to a specified recipient.

    Args:
    - recipient: The email address of the recipient.
    - subject: The subject line of the email.
    - body: The body content of the email.

    Sends a plain text email message using the configured email service.
    """
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype=MessageType.plain
    )
    await fm.send_message(message)


# Inactivity-specific email sender
async def send_inactivity_email(email: EmailStr, name: str) -> str:
    """
    Send an inactivity reminder email to a student.
    """
    body = (
        f"Hi {name},\n\n"
        "We noticed you haven't been active on LMS lately. "
        "Come back and continue your learning journey!\n\n"
        "Best,\nThe LMS Team"
    )
    message = MessageSchema(
        subject="We've missed you!",
        recipients=[email],
        body=body,
        subtype=MessageType.plain
    )
    await fm.send_message(message)
    return body

# Synchronous wrapper for daemon scripts
def send_inactivity_email_sync(email: EmailStr, name: str) -> str:
    """
    Synchronous wrapper for send_inactivity_email for use in daemon scripts.
    """
    return asyncio.run(send_inactivity_email(email, name))