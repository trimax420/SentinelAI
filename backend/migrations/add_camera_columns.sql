-- Add missing columns to cameras table
ALTER TABLE cameras
ADD COLUMN IF NOT EXISTS source VARCHAR(50),
ADD COLUMN IF NOT EXISTS zones JSONB,
ADD COLUMN IF NOT EXISTS last_active TIMESTAMP WITH TIME ZONE;

-- Create index on last_active
CREATE INDEX IF NOT EXISTS idx_cameras_last_active ON cameras(last_active); 