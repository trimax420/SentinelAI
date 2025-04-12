-- Drop existing analytics table
DROP TABLE IF EXISTS analytics CASCADE;

-- Recreate analytics table with correct column types
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    camera_id VARCHAR(50) REFERENCES cameras(camera_id) ON DELETE CASCADE,
    total_people INTEGER,
    people_per_zone JSONB DEFAULT '{}',
    movement_patterns JSONB DEFAULT '{}',
    dwell_times JSONB DEFAULT '{}',
    entry_count INTEGER DEFAULT 0,
    exit_count INTEGER DEFAULT 0
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_analytics_camera_id ON analytics(camera_id);
CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics(timestamp); 