-- Create analytics table
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    camera_id INTEGER REFERENCES cameras(camera_id) ON DELETE CASCADE,
    total_people INTEGER,
    people_per_zone JSONB,
    movement_patterns JSONB,
    dwell_times JSONB,
    entry_count INTEGER,
    exit_count INTEGER
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_camera_id ON analytics(camera_id); 