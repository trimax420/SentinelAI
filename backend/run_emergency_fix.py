import os
import psycopg2
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_emergency_fix():
    """Run emergency database fix"""
    # Load environment variables
    load_dotenv()
    
    # Get database connection parameters from environment
    db_params = {
        'dbname': os.getenv('POSTGRES_DB', 'surveillance'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'host': os.getenv('POSTGRES_SERVER', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }
    
    try:
        # Connect to PostgreSQL
        logger.info(f"Connecting to PostgreSQL database: {db_params['dbname']} on {db_params['host']}")
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # First drop existing tables to avoid dependency issues
        logger.info("Dropping dependent tables...")
        try:
            cursor.execute("DROP TABLE IF EXISTS detection_events CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS analytics CASCADE;")
            logger.info("Dropped detection_events and analytics tables")
        except Exception as e:
            logger.error(f"Error dropping existing tables: {str(e)}")
        
        # Create fresh cameras table with proper structure
        logger.info("Creating fresh cameras table...")
        try:
            # Create temp table with correct structure
            cursor.execute("""
            CREATE TABLE cameras_new (
                camera_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255),
                rtsp_url VARCHAR(255),
                source VARCHAR(255),
                zones JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                last_active TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """)
            
            # Check if old cameras table exists
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'cameras');")
            if cursor.fetchone()[0]:
                # Copy data from old table to new
                logger.info("Migrating data from old cameras table...")
                try:
                    # Check if old table has id column
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'id';")
                    has_id = cursor.fetchone() is not None
                    
                    # Check if old table has camera_id column
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'camera_id';")
                    has_camera_id = cursor.fetchone() is not None
                    
                    if has_id and not has_camera_id:
                        # If it has id but not camera_id, use id as camera_id
                        cursor.execute("""
                        INSERT INTO cameras_new (camera_id, name)
                        SELECT id, name FROM cameras;
                        """)
                    elif has_camera_id:
                        # If it has camera_id, use it directly
                        cursor.execute("""
                        INSERT INTO cameras_new (camera_id, name)
                        SELECT camera_id, name FROM cameras;
                        """)
                    
                    # Drop old table and rename new one
                    cursor.execute("DROP TABLE cameras CASCADE;")
                    cursor.execute("ALTER TABLE cameras_new RENAME TO cameras;")
                    logger.info("Successfully migrated cameras data")
                except Exception as e:
                    logger.error(f"Error migrating cameras data: {str(e)}")
                    raise
            else:
                # Just rename the new table
                cursor.execute("ALTER TABLE cameras_new RENAME TO cameras;")
                # Insert a default camera
                cursor.execute("""
                INSERT INTO cameras (camera_id, name, rtsp_url, source, is_active)
                VALUES ('cam001', 'Default Camera', 'rtsp://example.com/stream1', 'RTSP Stream', TRUE);
                """)
                logger.info("Created fresh cameras table with default camera")
            
        except Exception as e:
            logger.error(f"Error creating cameras table: {str(e)}")
            raise
        
        # Fix detection_events table
        logger.info("Creating detection_events table...")
        try:
            cursor.execute("""
            CREATE TABLE detection_events (
                id VARCHAR(50) PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                camera_id VARCHAR(50) REFERENCES cameras(camera_id) ON DELETE CASCADE,
                track_id VARCHAR(50),
                confidence FLOAT,
                detection_data JSONB,
                snapshot_path VARCHAR,
                video_clip_path VARCHAR,
                processed BOOLEAN DEFAULT FALSE,
                person_count INTEGER,
                x FLOAT,
                y FLOAT,
                frame_number INTEGER
            );
            """)
            
            logger.info("Successfully created detection_events table")
        except Exception as e:
            logger.error(f"Error creating detection_events table: {str(e)}")
            raise
        
        # Fix analytics table
        logger.info("Creating analytics table...")
        try:
            cursor.execute("""
            CREATE TABLE analytics (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                camera_id VARCHAR(50) REFERENCES cameras(camera_id) ON DELETE CASCADE,
                total_people INTEGER,
                people_per_zone JSONB,
                movement_patterns JSONB,
                dwell_times JSONB,
                entry_count INTEGER,
                exit_count INTEGER
            );
            """)
            
            logger.info("Successfully created analytics table")
        except Exception as e:
            logger.error(f"Error creating analytics table: {str(e)}")
            raise
        
        # Fix alerts table - add suspect_id if needed
        logger.info("Fixing alerts table...")
        try:
            # Check if alerts table exists
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alerts');")
            if cursor.fetchone()[0]:
                # Check if suspect_id column exists
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'alerts' AND column_name = 'suspect_id';")
                if cursor.fetchone() is None:
                    # Add suspect_id column if it doesn't exist
                    cursor.execute("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS suspect_id INTEGER;")
                    logger.info("Added suspect_id column to alerts table")
                else:
                    logger.info("suspect_id column already exists in alerts table")
            else:
                logger.warning("alerts table does not exist, skipping fix")
        except Exception as e:
            logger.error(f"Error fixing alerts table: {str(e)}")
            raise
        
        # Grant permissions
        cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;")
        
        logger.info("Emergency fix completed successfully!")
        
    except Exception as e:
        logger.error(f"Database emergency fix failed: {str(e)}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_emergency_fix() 