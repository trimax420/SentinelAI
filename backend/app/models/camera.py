# Add this to backend/app/models/camera.py
from sqlalchemy import Column, String, JSON, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class Camera(Base):
    __tablename__ = "cameras"
    
    camera_id = Column(String(50), primary_key=True, index=True)
    name = Column(String)
    source = Column(String)
    rtsp_url = Column(String)  # RTSP stream URL
    zones = Column(JSON, default={})  # Store zone coordinates as JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship with analytics - using string reference to avoid circular imports
    analytics = relationship("Analytics", back_populates="camera", cascade="all, delete-orphan")