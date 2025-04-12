-- Migration to fix feature vector column
ALTER TABLE suspect_images 
ALTER COLUMN feature_vector TYPE TEXT; 