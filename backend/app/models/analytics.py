from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    camera_id = Column(String(50), ForeignKey("cameras.camera_id", ondelete="CASCADE"))
    total_people = Column(Integer)
    people_per_zone = Column(JSON)  # Number of people in each zone
    movement_patterns = Column(JSON, nullable=True)  # Movement vectors between zones
    dwell_times = Column(JSON, nullable=True)  # Average time spent in each zone
    entry_count = Column(Integer, nullable=True)  # Number of people entering the frame
    exit_count = Column(Integer, nullable=True)  # Number of people exiting the frame
    
    # Relationship with camera - using string reference to avoid circular imports
    camera = relationship("Camera", back_populates="analytics", foreign_keys=[camera_id])

class HourlyFootfall(Base):
    __tablename__ = "hourly_footfall"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(100), index=True, nullable=False)
    timestamp_hour = Column(DateTime(timezone=True), index=True, nullable=False) # Start of the hour
    unique_person_count = Column(Integer, default=0)
    
    # Unique constraint to prevent duplicate entries for the same camera/hour
    # __table_args__ = (UniqueConstraint('camera_id', 'timestamp_hour', name='_camera_hour_uc'),)

class HourlyDemographics(Base):
    __tablename__ = "hourly_demographics"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(100), index=True, nullable=False)
    timestamp_hour = Column(DateTime(timezone=True), index=True, nullable=False) # Start of the hour
    demographics_data = Column(JSON) # Store counts like {"male_adult": 10, "female_young_adult": 5, ...}
    
    # Unique constraint
    # __table_args__ = (UniqueConstraint('camera_id', 'timestamp_hour', name='_demo_camera_hour_uc'),)