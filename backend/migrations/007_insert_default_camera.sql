-- Insert a default camera if it doesn't exist
INSERT INTO cameras (
    camera_id,
    name,
    description,
    location,
    rtsp_url,
    status
)
VALUES (
    'default_cam',
    'Main Entrance Camera',
    'Camera monitoring the main entrance',
    'Main Entrance',
    'rtsp://example.com/stream1',
    'active'
)
ON CONFLICT (camera_id) DO NOTHING; 