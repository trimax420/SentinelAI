-- Add missing columns to suspects table
ALTER TABLE suspects
ADD COLUMN IF NOT EXISTS aliases TEXT[],
ADD COLUMN IF NOT EXISTS physical_description TEXT,
ADD COLUMN IF NOT EXISTS biometric_markers JSONB,
ADD COLUMN IF NOT EXISTS priority_level INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Create index on priority_level
CREATE INDEX IF NOT EXISTS idx_suspects_priority_level ON suspects(priority_level); 