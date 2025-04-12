from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging
from sqlalchemy import inspect

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import settings
from app.core.config import settings

# Create SQLAlchemy engine using settings
SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

# Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_database_connection():
    """Verify database connection and print tables"""
    try:
        # Create database connection
        connection = engine.connect()
        
        # Get table names
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        logger.info(f"Successfully connected to database. Tables: {', '.join(table_names)}")
        connection.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False