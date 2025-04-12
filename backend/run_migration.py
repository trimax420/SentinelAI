import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Import settings
from app.core.config import settings

def run_migration():
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters from settings
    db_params = {
        'user': settings.POSTGRES_USER,
        'password': settings.POSTGRES_PASSWORD,
        'host': settings.POSTGRES_SERVER,
        'port': settings.POSTGRES_PORT,
        'dbname': settings.POSTGRES_DB
    }
    
    try:
        # Connect to the database
        print("Connecting to database...")
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Read and execute migration script
        print("Running migration to add suspect tables and columns...")
        with open('migrations/add_suspect_tables.sql', 'r') as f:
            migration_sql = f.read()
            cursor.execute(migration_sql)
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"An error occurred during migration: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migration()
