from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Text, Table, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

# Association table for suspect-case relationship
suspect_case_association = Table(
    'suspect_case_association',
    Base.metadata,
    Column('suspect_id', Integer, ForeignKey('suspects.id', ondelete="CASCADE")),
    Column('case_id', Integer, ForeignKey('cases.id', ondelete="CASCADE"))
)

class Suspect(Base):
    __tablename__ = "suspects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    aliases = Column(ARRAY(String))  # List of known aliases
    physical_description = Column(Text)
    biometric_markers = Column(JSON)  # Facial features, height, weight, etc.
    priority_level = Column(Integer, default=1)  # 1-5 scale
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    images = relationship("SuspectImage", back_populates="suspect", cascade="all, delete-orphan")
    locations = relationship("SuspectLocation", back_populates="suspect", cascade="all, delete-orphan")
    cases = relationship("Case", secondary=suspect_case_association, back_populates="suspects")
    alerts = relationship("Alert", back_populates="suspect")

class SuspectImage(Base):
    __tablename__ = "suspect_images"
    
    id = Column(Integer, primary_key=True, index=True)
    suspect_id = Column(Integer, ForeignKey("suspects.id", ondelete="CASCADE"))
    image_path = Column(String(255), nullable=False)
    thumbnail_path = Column(String(255))
    feature_vector = Column(Text)  # Changed from JSON to Text to ensure consistent storage format
    confidence_score = Column(Float)
    capture_date = Column(DateTime(timezone=True))
    source = Column(String(100))  # CCTV, mugshot, etc.
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    suspect = relationship("Suspect", back_populates="images")

class SuspectLocation(Base):
    __tablename__ = "suspect_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    suspect_id = Column(Integer, ForeignKey("suspects.id", ondelete="CASCADE"))
    camera_id = Column(Integer, ForeignKey("cameras.camera_id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    confidence = Column(Float)
    coordinates = Column(JSON)  # x, y coordinates in frame
    movement_vector = Column(JSON)  # Direction and speed of movement
    frame_number = Column(Integer)
    
    # Relationship
    suspect = relationship("Suspect", back_populates="locations")

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    status = Column(String(50))  # open, closed, pending, etc.
    priority = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    suspects = relationship("Suspect", secondary=suspect_case_association, back_populates="cases") 