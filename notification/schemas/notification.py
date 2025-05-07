"""
Pydantic schemas for handling notifications data.

- `NotificationCreate`: Schema for creating a new notification. It includes:
  - `user_id`: The ID of the user receiving the notification.
  - `message`: The content of the notification.

- `NotificationResponse`: Schema for serializing notification data in API responses. It includes:
  - `id`: The unique identifier of the notification.
  - `user_id`: The ID of the user receiving the notification.
  - `message`: The content of the notification.
  - `sent_at`: The timestamp when the notification was sent.

The `Config` class in `NotificationResponse` ensures that attributes are returned from the model when serialized.
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: int
    message: str

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    sent_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)
