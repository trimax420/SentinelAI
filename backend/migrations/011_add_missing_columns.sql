-- Add missing columns to detection_events table
ALTER TABLE detection_events
ADD COLUMN IF NOT EXISTS snapshot_path VARCHAR(255),
ADD COLUMN IF NOT EXISTS video_clip_path VARCHAR(255),
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS person_count INTEGER,
ADD COLUMN IF NOT EXISTS x FLOAT,
ADD COLUMN IF NOT EXISTS y FLOAT;

-- Add index for processed column
CREATE INDEX IF NOT EXISTS idx_detection_events_processed ON detection_events(processed); 