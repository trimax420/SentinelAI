-- Add person_count column to detection_events table
ALTER TABLE detection_events ADD COLUMN IF NOT EXISTS person_count INTEGER; 