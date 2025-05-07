"""
Email log model for tracking outbound emails.

Defines the `EmailLog` SQLAlchemy model used to store information about
emails sent from the system, including recipient, subject, body, and
timestamp.

Table: email_logs
"""

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database.database import Base

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)


from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database.database import Base

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
