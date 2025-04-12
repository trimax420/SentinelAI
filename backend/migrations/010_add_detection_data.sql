-- Add detection_data column to detection_events table
ALTER TABLE detection_events
ADD COLUMN IF NOT EXISTS detection_data JSONB DEFAULT '{}';

-- Add index for detection_data
CREATE INDEX IF NOT EXISTS idx_detection_events_data ON detection_events USING GIN (detection_data); 