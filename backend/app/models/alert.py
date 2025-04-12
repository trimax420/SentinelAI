from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    alert_type = Column(String(50), nullable=False)  # Ensure this matches the database
    severity = Column(Integer, nullable=False)
    track_id = Column(String(50))
    description = Column(Text)
    snapshot_path = Column(String(255))
    video_clip_path = Column(String(255))
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime(timezone=True))
    
    # Add suspect relationship
    suspect_id = Column(Integer, ForeignKey("suspects.id", ondelete="SET NULL"), nullable=True)
    suspect = relationship("Suspect", back_populates="alerts")