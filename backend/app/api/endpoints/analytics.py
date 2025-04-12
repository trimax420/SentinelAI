# app/api/endpoints/analytics.py (simplified)
# app/api/endpoints/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.schemas.analytics import Analytics as AnalyticsSchema, DailyTrafficSummary
from app.models.analytics import Analytics as AnalyticsModel, HourlyFootfall, HourlyDemographics
from app.services.analytics import calculate_daily_summary, get_zone_dwell_times
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[AnalyticsSchema])
async def get_analytics(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get analytics with optional time filtering
    """
    query = db.query(AnalyticsModel)
    
    if start_time:
        query = query.filter(AnalyticsModel.timestamp >= start_time)
    if end_time:
        query = query.filter(AnalyticsModel.timestamp <= end_time)
    
    analytics = query.order_by(AnalyticsModel.timestamp.desc()).limit(limit).all()
    return analytics

@router.get("/current/", response_model=dict)
async def get_current_metrics(db: Session = Depends(get_db)):
    """
    Get current real-time metrics for the dashboard
    """
    try:
        # Get latest analytics record
        latest = db.query(AnalyticsModel).order_by(AnalyticsModel.timestamp.desc()).first()
        
        if not latest:
            return {
                "totalPeople": 0,
                "zoneOccupancy": {},
                "dwellTimes": {},
                "movementPatterns": {}
            }
        
        return {
            "totalPeople": latest.total_people or 0,
            "zoneOccupancy": latest.people_per_zone or {},
            "dwellTimes": latest.dwell_times or {},
            "movementPatterns": latest.movement_patterns or {}
        }
        
    except Exception as e:
        logger.error(f"Error getting current metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve current metrics")

@router.post("/analytics/", response_model=AnalyticsSchema)
def create_analytics(
    analytics: AnalyticsSchema,
    db: Session = Depends(get_db)
):
    db_analytics = AnalyticsModel(**analytics.dict())
    db.add(db_analytics)
    db.commit()
    db.refresh(db_analytics)
    return db_analytics

@router.get("/daily-traffic-summary/", response_model=DailyTrafficSummary)
def get_daily_traffic_summary(
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        summary = calculate_daily_summary(db, date)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/zone-analytics/")
def get_zone_analytics(
    camera_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AnalyticsModel).filter(AnalyticsModel.camera_id == camera_id)
    
    if start_date:
        query = query.filter(AnalyticsModel.timestamp >= start_date)
    if end_date:
        query = query.filter(AnalyticsModel.timestamp <= end_date)
    
    analytics_data = query.all()
    
    zone_analytics = {}
    for entry in analytics_data:
        if entry.people_per_zone:
            for zone, count in entry.people_per_zone.items():
                if zone not in zone_analytics:
                    zone_analytics[zone] = 0
                zone_analytics[zone] += count
    
    return {
        "camera_id": camera_id,
        "zone_occupancy": zone_analytics,
        "total_entries": len(analytics_data)
    }

@router.get("/zone-dwell-times/")
def analyze_zone_dwell_times(
    camera_id: int,
    zone_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis of dwell times in specific camera zones.
    
    Parameters:
    - camera_id: ID of the camera to analyze
    - zone_name: (Optional) Specific zone to analyze. If not provided, analyzes all zones
    - start_date: (Optional) Start date for analysis
    - end_date: (Optional) End date for analysis
    """
    try:
        results = get_zone_dwell_times(
            db=db,
            camera_id=camera_id,
            zone_name=zone_name,
            start_date=start_date,
            end_date=end_date
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class FootfallResponse(BaseModel):
    camera_id: str
    timestamp_hour: datetime
    unique_person_count: int

    class Config:
        orm_mode = True

class DemographicsResponse(BaseModel):
    camera_id: str
    timestamp_hour: datetime
    demographics_data: dict

    class Config:
        orm_mode = True

@router.get("/footfall", response_model=List[FootfallResponse])
async def get_hourly_footfall(
    start_time: datetime, 
    end_time: datetime,
    camera_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get hourly footfall data within a time range, optionally filtered by camera."""
    query = db.query(HourlyFootfall)
    query = query.filter(HourlyFootfall.timestamp_hour >= start_time)
    query = query.filter(HourlyFootfall.timestamp_hour < end_time) # Use < for end_time
    if camera_id:
        query = query.filter(HourlyFootfall.camera_id == camera_id)
        
    results = query.order_by(HourlyFootfall.camera_id, HourlyFootfall.timestamp_hour).all()
    return results

@router.get("/demographics", response_model=List[DemographicsResponse])
async def get_hourly_demographics(
    start_time: datetime, 
    end_time: datetime,
    camera_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get hourly demographics data within a time range, optionally filtered by camera."""
    query = db.query(HourlyDemographics)
    query = query.filter(HourlyDemographics.timestamp_hour >= start_time)
    query = query.filter(HourlyDemographics.timestamp_hour < end_time)
    if camera_id:
        query = query.filter(HourlyDemographics.camera_id == camera_id)
        
    results = query.order_by(HourlyDemographics.camera_id, HourlyDemographics.timestamp_hour).all()
    return results