# backend/app/schemas/camera.py
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class CameraBase(BaseModel):
    camera_id: str
    name: Optional[str] = None
    location: Optional[str] = None
    source: str
    is_active: Optional[bool] = True

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    is_active: Optional[bool] = None

class Camera(CameraBase):
    created_at: datetime
    last_active: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # For SQLAlchemy model compatibility