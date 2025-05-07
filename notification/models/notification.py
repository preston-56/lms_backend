"""
Notification Model
==================

Defines the `Notification` SQLAlchemy model used for storing notification messages
sent to users within the LMS system.

Attributes:
- `id`: Primary key identifier for each notification.
- `user_id`: Foreign key linking the notification to a user.
- `message`: The content/message of the notification.
- `sent_at`: Timestamp indicating when the notification was sent (default is current UTC time).

Relationships:
- `user`: Establishes a many-to-one relationship with the `User` model,
          allowing access to the recipient of the notification.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
