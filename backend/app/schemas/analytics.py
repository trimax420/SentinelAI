# app/schemas/analytics.py
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class AnalyticsBase(BaseModel):
    camera_id: int
    total_people: int
    people_per_zone: Dict[str, int]
    movement_patterns: Optional[Dict[str, List[Dict[str, Any]]]] = None
    dwell_times: Optional[Dict[str, float]] = None
    entry_count: Optional[int] = None
    exit_count: Optional[int] = None

class AnalyticsCreate(AnalyticsBase):
    pass

class Analytics(AnalyticsBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class DailyTrafficSummary(BaseModel):
    date: str
    total_entries: int
    total_exits: int
    peak_hours: Dict[str, int]
    zone_occupancy: Dict[str, int]
    average_dwell_times: Dict[str, float]
    busiest_zones: List[Dict[str, Any]]
    movement_heatmap: Dict[str, Dict[str, int]]

    class Config:
        orm_mode = True