-- Add x and y coordinate columns to detection_events table
ALTER TABLE detection_events ADD COLUMN IF NOT EXISTS x FLOAT;
ALTER TABLE detection_events ADD COLUMN IF NOT EXISTS y FLOAT; 