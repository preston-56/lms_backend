"""
Database configuration and session management.

- Loads database URL from environment variables using dotenv.
- Sets up SQLAlchemy engine and session factory.
- Defines a shared declarative base for all models.
- Provides a `get_db` dependency for FastAPI routes to access the database session.
- Imports all models via the centralized models module to ensure they're registered with SQLAlchemy.

Environment Variables:
- DATABASE_URL: Connection string to the PostgreSQL or other supported database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
"""
The engine manages the connection to the database and handles query execution.
"""
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Import all models to register them with SQLAlchemy's metadata
import models

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
