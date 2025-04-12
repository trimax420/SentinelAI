import os
import sys
from sqlalchemy import text
from app.core.database import engine

def run_migration(sql_file):
    """Run a SQL migration file"""
    if not os.path.exists(sql_file):
        # Check if it's in the migrations folder
        migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'migrations')
        test_path = os.path.join(migrations_dir, sql_file)
        if os.path.exists(test_path):
            sql_file = test_path
        else:
            print(f"Migration file not found: {sql_file}")
            return False
    
    print(f"Running migration from: {sql_file}")
    
    # Read the SQL file
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    # Execute the SQL
    with engine.connect() as conn:
        print(f"Executing SQL: {sql}")
        result = conn.execute(text(sql))
        conn.commit()
    
    print("Migration completed successfully")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.scripts.run_migration <sql_file>")
        sys.exit(1)
    
    sql_file = sys.argv[1]
    success = run_migration(sql_file)
    if not success:
        sys.exit(1) 