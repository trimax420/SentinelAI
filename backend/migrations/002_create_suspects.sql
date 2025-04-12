-- Create suspects table
CREATE TABLE IF NOT EXISTS suspects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    risk_level INTEGER DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_suspects_status ON suspects(status);
CREATE INDEX IF NOT EXISTS idx_suspects_risk_level ON suspects(risk_level); 