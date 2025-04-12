-- Add rtsp_url column to cameras table
ALTER TABLE cameras ADD COLUMN IF NOT EXISTS rtsp_url VARCHAR; 