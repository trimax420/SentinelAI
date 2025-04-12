import os
import psycopg2
from dotenv import load_dotenv

# Import settings
from app.core.config import settings

def run_detection_migration():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get database connection parameters from settings
    db_params = {
        'dbname': settings.POSTGRES_DB,
        'user': settings.POSTGRES_USER,
        'password': settings.POSTGRES_PASSWORD,
        'host': settings.POSTGRES_SERVER,
        'port': settings.POSTGRES_PORT
    }
    
    # Connect to PostgreSQL
    print("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(**db_params)
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Execute the migration script
        print("Running migration to update detection_events table...")
        with open('migrations/update_detection_events.sql', 'r') as f:
            sql = f.read()
        cursor.execute(sql)
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_detection_migration() 