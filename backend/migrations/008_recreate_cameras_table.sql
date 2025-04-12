-- Drop existing table and recreate with correct column types
DROP TABLE IF EXISTS cameras CASCADE;

-- Recreate cameras table with correct column types
CREATE TABLE IF NOT EXISTS cameras (
    camera_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    is_active BOOLEAN DEFAULT TRUE,
    rtsp_url VARCHAR(255),
    source VARCHAR(255),
    username VARCHAR(100),
    password VARCHAR(100),
    fps INTEGER DEFAULT 30,
    resolution_width INTEGER,
    resolution_height INTEGER,
    zones JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP WITH TIME ZONE
);

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_cameras_name ON cameras(name);
CREATE INDEX IF NOT EXISTS idx_cameras_status ON cameras(status);
CREATE INDEX IF NOT EXISTS idx_cameras_is_active ON cameras(is_active); 