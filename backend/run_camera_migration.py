from sqlalchemy import create_engine, Column, Integer, String, JSON, Boolean, DateTime, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_camera_migration():
    try:
        # Create database engine
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Update cameras table
        logger.info("Updating cameras table...")
        
        # Drop existing table if it exists
        db.execute(text("DROP TABLE IF EXISTS cameras CASCADE"))
        
        # Create new table with updated schema
        db.execute(text("""
            CREATE TABLE cameras (
                id SERIAL PRIMARY KEY,
                name VARCHAR UNIQUE,
                rtsp_url VARCHAR,
                zones JSONB,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP WITH TIME ZONE,
                CONSTRAINT unique_camera_name UNIQUE (name)
            )
        """))
        
        db.commit()
        logger.info("Successfully updated cameras table")
        
    except Exception as e:
        logger.error(f"Error during camera migration: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_camera_migration() 