import os
import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations"""
    try:
        # Get the path to the migrations directory
        migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'migrations')
        
        # Get all SQL files and sort them
        migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.sql')]
        # Sort files to ensure numbered migrations run in order
        migration_files.sort()
        
        # Read and execute each SQL file
        for filename in migration_files:
            file_path = os.path.join(migrations_dir, filename)
            with open(file_path, 'r') as f:
                sql = f.read()
                
            with engine.connect() as connection:
                # Wrap each migration in a transaction
                trans = connection.begin()
                try:
                    connection.execute(text(sql))
                    trans.commit()
                    logger.info(f"Successfully executed migration: {filename}")
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Failed to execute migration {filename}: {str(e)}")
                    raise
                
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migrations() 