-- Create detection_events table
CREATE TABLE IF NOT EXISTS detection_events (
    id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    camera_id VARCHAR(50) NOT NULL,
    track_id VARCHAR(50),
    confidence FLOAT,
    detection_data JSONB DEFAULT '{}',
    snapshot_path VARCHAR(255),
    video_clip_path VARCHAR(255),
    processed BOOLEAN DEFAULT FALSE,
    person_count INTEGER,
    x FLOAT,
    y FLOAT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_detection_events_timestamp ON detection_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_detection_events_camera_id ON detection_events(camera_id);
CREATE INDEX IF NOT EXISTS idx_detection_events_track_id ON detection_events(track_id);
CREATE INDEX IF NOT EXISTS idx_detection_events_data ON detection_events USING GIN (detection_data); 