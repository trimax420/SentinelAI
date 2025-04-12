# app/schemas/alert.py
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class AlertBase(BaseModel):
    alert_type: str
    severity: int
    track_id: Optional[str] = None
    description: Optional[str] = None

class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    acknowledged: Optional[bool] = None
    acknowledged_by: Optional[str] = None

class Alert(AlertBase):
    id: int
    timestamp: datetime
    snapshot_path: Optional[str] = None
    video_clip_path: Optional[str] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True