-- Create suspect_images table
CREATE TABLE IF NOT EXISTS suspect_images (
    id SERIAL PRIMARY KEY,
    suspect_id INTEGER NOT NULL REFERENCES suspects(id) ON DELETE CASCADE,
    image_path VARCHAR(255) NOT NULL,
    thumbnail_path VARCHAR(255),
    feature_vector BYTEA,
    confidence_score FLOAT,
    capture_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on suspect_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_suspect_images_suspect_id ON suspect_images(suspect_id);

-- Create index on is_primary for faster primary image lookups
CREATE INDEX IF NOT EXISTS idx_suspect_images_is_primary ON suspect_images(is_primary); 