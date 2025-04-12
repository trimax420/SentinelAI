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

def run_migrations():
    """Run database migrations from SQL files"""
    # Load environment variables
    load_dotenv()
    
    # Get database connection parameters from environment
    db_params = {
        'dbname': os.getenv('POSTGRES_DB', 'surveillance'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'host': os.getenv('POSTGRES_SERVER', '3.29.236.57'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }
    
    # List of migration files to run (in order)
    migration_files = [
        'migrations/database_schema.sql',
        'migrations/create_alerts_table.sql',
        'migrations/update_detection_events.sql',
        'migrations/update_alerts.sql',
        'migrations/create_camera.sql',
        'migrations/update_cameras_table.sql',
        'migrations/add_suspect_tables.sql',
        'migrations/update_suspects_table.sql',
        'migrations/add_rtsp_url.sql',  # Add rtsp_url column
        'migrations/add_person_count.sql',  # Add person_count column
        'migrations/add_coordinates.sql',  # Add x and y coordinate columns
        'migrations/create_analytics_table.sql',  # Create analytics table
        'migrations/fix_detection_events.sql',  # Fix detection_events table
        'migrations/fix_database.sql'  # Comprehensive fix for database issues
    ]
    
    try:
        # Connect to PostgreSQL
        logger.info(f"Connecting to PostgreSQL database: {db_params['dbname']} on {db_params['host']}")
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Run each migration file
        for migration_file in migration_files:
            try:
                logger.info(f"Running migration: {migration_file}")
                
                with open(migration_file, 'r') as f:
                    sql = f.read()
                    
                cursor.execute(sql)
                logger.info(f"Successfully executed: {migration_file}")
                
            except Exception as e:
                logger.error(f"Error executing migration {migration_file}: {str(e)}")
                raise
        
        logger.info("All migrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Database migration failed: {str(e)}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migrations()
