# rfiprocessor/db/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..utils.logger import get_logger

logger = get_logger(__name__)

# For development, we'll use a local SQLite database.
# The connection string can be updated for production (e.g., Azure).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/db/rfi_processor.db")

# Create the SQLAlchemy engine
# `connect_args` is specific to SQLite to allow multi-threaded access.
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False  # Set to True to see generated SQL statements
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our ORM models to inherit from
Base = declarative_base()

def init_db():
    """
    Initializes the database by creating all tables defined by models
    that inherit from the Base class.
    """
    try:
        logger.info("Initializing database and creating tables if they don't exist...")
        # Create the directory for the SQLite DB if it doesn't exist
        if 'sqlite' in DATABASE_URL:
            db_path = DATABASE_URL.split('///')[1]
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise

def get_db_session():
    """
    Dependency function to get a database session.
    Ensures the session is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()