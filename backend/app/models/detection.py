from sqlalchemy import Column, String, Float, DateTime, JSON, Integer, Boolean, ForeignKey, text
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id = Column(String(50), primary_key=True, default=lambda: f"det_{uuid.uuid4().hex[:8]}")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    camera_id = Column(String(50), ForeignKey('cameras.camera_id'))
    track_id = Column(String(50))
    confidence = Column(Float)
    detection_data = Column(JSON)
    snapshot_path = Column(String)
    video_clip_path = Column(String)
    processed = Column(Boolean, default=False)
    person_count = Column(Integer)  # Number of people detected in the frame
    x = Column(Float)  # X coordinate of detection
    y = Column(Float)  # Y coordinate of detection
