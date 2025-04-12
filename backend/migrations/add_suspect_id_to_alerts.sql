-- Add suspect_id column to alerts table
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS suspect_id INTEGER; 