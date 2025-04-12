import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Import settings
from app.core.config import settings

def init_db():
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters from settings
    db_params = {
        'user': settings.POSTGRES_USER,
        'password': settings.POSTGRES_PASSWORD,
        'host': settings.POSTGRES_SERVER,
        'port': settings.POSTGRES_PORT
    }
    
    database_name = settings.POSTGRES_DB
    
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (database_name,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database: {database_name}")
            cursor.execute(f'CREATE DATABASE {database_name}')
            print("Database created successfully!")
        else:
            print(f"Database '{database_name}' already exists")
        
        cursor.close()
        conn.close()
        
        # Connect to the newly created database
        db_params['dbname'] = database_name
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create tables
        print("Creating tables...")
        cursor.execute("""
            -- Create cameras table
            CREATE TABLE IF NOT EXISTS cameras (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                location VARCHAR(255),
                stream_url VARCHAR(255),
                status VARCHAR(50) DEFAULT 'offline',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );

            -- Create suspects table
            CREATE TABLE IF NOT EXISTS suspects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );

            -- Create detection_events table
            CREATE TABLE IF NOT EXISTS detection_events (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                camera_id INTEGER REFERENCES cameras(id),
                track_id VARCHAR(50),
                confidence FLOAT,
                detection_data JSONB,
                snapshot_path VARCHAR(255),
                video_clip_path VARCHAR(255),
                processed BOOLEAN DEFAULT FALSE
            );

            -- Create alerts table
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                alert_type VARCHAR(50) NOT NULL,
                severity INTEGER NOT NULL,
                track_id VARCHAR(50),
                description TEXT,
                snapshot_path VARCHAR(255),
                video_clip_path VARCHAR(255),
                acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by VARCHAR(100),
                acknowledged_at TIMESTAMP WITH TIME ZONE,
                detection_id INTEGER REFERENCES detection_events(id),
                suspect_id INTEGER REFERENCES suspects(id) ON DELETE SET NULL
            );

            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
            CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
            CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
            CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);
            CREATE INDEX IF NOT EXISTS idx_alerts_suspect ON alerts(suspect_id);
            
            CREATE INDEX IF NOT EXISTS idx_detection_timestamp ON detection_events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_detection_camera ON detection_events(camera_id);
            CREATE INDEX IF NOT EXISTS idx_detection_track ON detection_events(track_id);

            -- Add suspect_id column to alerts table if it doesn't exist
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'alerts' AND column_name = 'suspect_id'
                ) THEN
                    ALTER TABLE alerts ADD COLUMN suspect_id INTEGER REFERENCES suspects(id) ON DELETE SET NULL;
                END IF;
            END $$;
        """)
        
        print("Tables created successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_db()
