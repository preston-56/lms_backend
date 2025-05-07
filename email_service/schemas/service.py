"""
Pydantic schemas for the email service.

- `EmailRequest`: Defines the structure for incoming email send requests.
- `EmailLogResponse`: Defines the structure of an email log entry returned from the database.

Used for validating and serializing request and response data in email-related API endpoints.
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class EmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    body: str

class EmailLogResponse(BaseModel):
    id: int
    recipient: EmailStr
    subject: str
    body: str
    sent_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)
