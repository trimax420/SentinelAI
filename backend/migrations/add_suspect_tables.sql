-- Create suspects table if it doesn't exist
CREATE TABLE IF NOT EXISTS suspects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create suspect_images table if it doesn't exist
CREATE TABLE IF NOT EXISTS suspect_images (
    id SERIAL PRIMARY KEY,
    suspect_id INTEGER REFERENCES suspects(id) ON DELETE CASCADE,
    image_path VARCHAR(255) NOT NULL,
    thumbnail_path VARCHAR(255),
    feature_vector JSONB,
    confidence_score FLOAT,
    capture_date TIMESTAMP WITH TIME ZONE,
    source VARCHAR(100),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create suspect_locations table if it doesn't exist
CREATE TABLE IF NOT EXISTS suspect_locations (
    id SERIAL PRIMARY KEY,
    suspect_id INTEGER REFERENCES suspects(id) ON DELETE CASCADE,
    camera_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence FLOAT,
    coordinates JSONB,
    movement_vector JSONB,
    frame_number INTEGER
);

-- Create cases table if it doesn't exist
CREATE TABLE IF NOT EXISTS cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(50) UNIQUE,
    title VARCHAR(200),
    description TEXT,
    status VARCHAR(50),
    priority INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create suspect_case_association table if it doesn't exist
CREATE TABLE IF NOT EXISTS suspect_case_association (
    suspect_id INTEGER REFERENCES suspects(id) ON DELETE CASCADE,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    PRIMARY KEY (suspect_id, case_id)
);

-- Add suspect_id to alerts table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'alerts' AND column_name = 'suspect_id'
    ) THEN
        ALTER TABLE alerts ADD COLUMN suspect_id INTEGER REFERENCES suspects(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_alerts_suspect ON alerts(suspect_id);
CREATE INDEX IF NOT EXISTS idx_suspect_images_suspect ON suspect_images(suspect_id);
CREATE INDEX IF NOT EXISTS idx_suspect_locations_suspect ON suspect_locations(suspect_id);
CREATE INDEX IF NOT EXISTS idx_suspect_locations_camera ON suspect_locations(camera_id);
CREATE INDEX IF NOT EXISTS idx_cases_number ON cases(case_number); 