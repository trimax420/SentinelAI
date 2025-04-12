from sqlalchemy import create_engine, Column, Integer, String, JSON, Boolean, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_analytics_migration():
    try:
        # Create database engine
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Update analytics table
        logger.info("Updating analytics table...")
        
        # Drop existing table if it exists
        db.execute(text("DROP TABLE IF EXISTS analytics CASCADE"))
        
        # Create new table with updated schema
        db.execute(text("""
            CREATE TABLE analytics (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                camera_id INTEGER REFERENCES cameras(id) ON DELETE CASCADE,
                total_people INTEGER,
                people_per_zone JSONB,
                movement_patterns JSONB,
                dwell_times JSONB,
                entry_count INTEGER,
                exit_count INTEGER
            )
        """))
        
        db.commit()
        logger.info("Successfully updated analytics table")
        
    except Exception as e:
        logger.error(f"Error during analytics migration: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_analytics_migration() 