from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class DetectionBase(BaseModel):
    x: float
    y: float
    confidence: float
    camera_id: str
    detection_data: Optional[Dict[str, Any]] = None
    frame_number: Optional[int] = None
    person_count: Optional[int] = None

class DetectionCreate(DetectionBase):
    pass

class Detection(DetectionBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy model compatibility 