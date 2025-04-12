-- Create hourly_footfall table
CREATE TABLE IF NOT EXISTS hourly_footfall (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(100) NOT NULL,
    timestamp_hour TIMESTAMPTZ NOT NULL, -- Start of the hour
    unique_person_count INTEGER DEFAULT 0,
    CONSTRAINT _footfall_camera_hour_uc UNIQUE (camera_id, timestamp_hour)
);
CREATE INDEX IF NOT EXISTS idx_hourly_footfall_camera_id ON hourly_footfall(camera_id);
CREATE INDEX IF NOT EXISTS idx_hourly_footfall_timestamp_hour ON hourly_footfall(timestamp_hour);

-- Create hourly_demographics table
CREATE TABLE IF NOT EXISTS hourly_demographics (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(100) NOT NULL,
    timestamp_hour TIMESTAMPTZ NOT NULL, -- Start of the hour
    demographics_data JSONB, -- Using JSONB for better indexing if needed
    CONSTRAINT _demographics_camera_hour_uc UNIQUE (camera_id, timestamp_hour)
);
CREATE INDEX IF NOT EXISTS idx_hourly_demographics_camera_id ON hourly_demographics(camera_id);
CREATE INDEX IF NOT EXISTS idx_hourly_demographics_timestamp_hour ON hourly_demographics(timestamp_hour); 