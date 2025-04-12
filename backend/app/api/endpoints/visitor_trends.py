from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import func, cast, Date, Time, extract, and_, or_, distinct
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import literal_column
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, time
import calendar
import os
import logging

from app.core.database import get_db
from app.models.detection import DetectionEvent
from app.models.analytics import Analytics
from app.services.detector import DetectionService
from app.services.tracker import PersonTracker
from app.services.behavior import BehaviorAnalysisService
from app.utils.video import process_video_file

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
detector_service = DetectionService()
tracker_service = PersonTracker()
behavior_service = BehaviorAnalysisService()

@router.get("/daily-trends/", response_model=Dict)
async def get_daily_visitor_trends(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = Query("hourly", description="Data aggregation interval: hourly, daily, weekly"),
    camera_id: Optional[str] = Query(None, description="Filter by specific camera"),
    db: Session = Depends(get_db)
):
    """
    Get daily visitor trends data for visualization
    
    - Returns visitor counts aggregated by chosen interval
    - Supports different time ranges and aggregation intervals
    - Can be used for time-series charts
    - Filter by specific camera or get data across all cameras
    """
    # Set default date range if not provided (last 7 days)
    if not end_date:
        end_date = datetime.now().date()
    else:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
    if not start_date:
        start_date = end_date - timedelta(days=7)
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    
    # Convert to datetime for database query
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)
    
    # Get analytics data directly from detection events for more accuracy
    query = db.query(
        DetectionEvent.timestamp, 
        DetectionEvent.camera_id,
        DetectionEvent.person_count
    ).filter(
        DetectionEvent.timestamp >= start_datetime,
        DetectionEvent.timestamp <= end_datetime
    )
    
    # Apply camera filter if specified
    if camera_id:
        query = query.filter(DetectionEvent.camera_id == camera_id)
    
    # Execute query to get raw data
    detection_data = query.order_by(DetectionEvent.timestamp).all()
    
    if not detection_data:
        return {
            "interval": interval,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "camera_id": camera_id,
            "trends": []
        }
    
    # Process data based on the selected interval
    if interval == "hourly":
        trends = process_hourly_trends(detection_data, start_datetime, end_datetime)
    elif interval == "daily":
        trends = process_daily_trends(detection_data, start_date, end_date)
    elif interval == "weekly":
        trends = process_weekly_trends(detection_data, start_date, end_date)
    else:
        raise HTTPException(status_code=400, detail="Invalid interval. Use 'hourly', 'daily', or 'weekly'")
    
    # Get camera list for reference
    camera_list = get_camera_list(db)
    
    return {
        "interval": interval,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "camera_id": camera_id,
        "trends": trends,
        "cameras": camera_list
    }

@router.get("/peak-hours/", response_model=Dict)
async def get_peak_hours(
    days: int = Query(30, description="Number of days to include in analysis"),
    day_type: Optional[str] = Query(None, description="Filter by day type: weekday, weekend, all"),
    camera_id: Optional[str] = Query(None, description="Filter by specific camera"),
    db: Session = Depends(get_db)
):
    """
    Get peak hour analysis showing busiest times
    
    - Returns visitor counts aggregated by hour of day
    - Can filter for weekdays, weekends, or all days
    - Calculates average values across the selected date range
    - Supports filtering by camera ID
    """
    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Convert to datetime for database query
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)
    
    # Get analytics data from database
    base_query = db.query(
        extract('hour', DetectionEvent.timestamp).label('hour'),
        func.avg(DetectionEvent.person_count).label('avg_count'),
        func.max(DetectionEvent.person_count).label('max_count'),
        func.min(DetectionEvent.person_count).label('min_count')
    )
    
    # Apply time range filter
    query = base_query.filter(
        DetectionEvent.timestamp >= start_datetime,
        DetectionEvent.timestamp <= end_datetime
    )
    
    # Apply camera filter if specified
    if camera_id:
        query = query.filter(DetectionEvent.camera_id == camera_id)
    
    # Apply day type filter if specified
    if day_type:
        if day_type.lower() == 'weekday':
            # Monday=0, Friday=4 in some DB systems, 1-5 in others
            # Extract dow returns 0-6, where 0 is Sunday in some DB systems
            query = query.filter(extract('dow', DetectionEvent.timestamp).between(1, 5))
        elif day_type.lower() == 'weekend':
            # Saturday=5, Sunday=6 or 0
            query = query.filter(or_(
                extract('dow', DetectionEvent.timestamp) == 0,
                extract('dow', DetectionEvent.timestamp) == 6
            ))
        elif day_type.lower() != 'all':
            raise HTTPException(status_code=400, detail="Invalid day_type. Use 'weekday', 'weekend', or 'all'")
    
    # Group by hour and get results
    query = query.group_by('hour').order_by('hour')
    hourly_data = query.all()
    
    # Format results
    hours = []
    for hour, avg_count, max_count, min_count in hourly_data:
        hours.append({
            "hour": hour,
            "hour_formatted": f"{hour}:00-{(hour+1) % 24}:00",
            "average_count": round(float(avg_count), 1) if avg_count else 0,
            "max_count": int(max_count) if max_count else 0,
            "min_count": int(min_count) if min_count else 0,
        })
    
    # Calculate peak hours (top 3)
    peak_hours = sorted(hours, key=lambda x: x["average_count"], reverse=True)[:3]
    
    # Get camera list for reference
    camera_list = get_camera_list(db)
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "day_type": day_type or "all",
        "camera_id": camera_id,
        "hours": hours,
        "peak_hours": peak_hours,
        "cameras": camera_list,
        "summary": {
            "busiest_hour": peak_hours[0]["hour_formatted"] if peak_hours else None,
            "total_hours_analyzed": len(hours),
            "days_analyzed": days
        }
    }

@router.get("/heatmap/", response_model=Dict)
async def get_traffic_heatmap(
    days: int = Query(30, description="Number of days to include"),
    camera_id: Optional[str] = Query(None, description="Filter by specific camera"),
    db: Session = Depends(get_db)
):
    """
    Get traffic heatmap data (day of week vs. hour of day)
    
    - Returns a 2D matrix of traffic patterns
    - Shows busiest day-hour combinations
    - Useful for creating heatmap visualizations
    - Supports filtering by camera ID
    """
    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Convert to datetime for database query
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)
    
    # Get analytics data from database with day of week and hour
    query = db.query(
        extract('dow', DetectionEvent.timestamp).label('day_of_week'),
        extract('hour', DetectionEvent.timestamp).label('hour'),
        func.avg(DetectionEvent.person_count).label('avg_count')
    ).filter(
        DetectionEvent.timestamp >= start_datetime,
        DetectionEvent.timestamp <= end_datetime
    )
    
    # Apply camera filter if specified
    if camera_id:
        query = query.filter(DetectionEvent.camera_id == camera_id)
        
    # Group and order
    query = query.group_by('day_of_week', 'hour').order_by('day_of_week', 'hour')
    
    heatmap_data = query.all()
    
    # Initialize empty heatmap matrix (7 days x 24 hours)
    heatmap_matrix = []
    for day in range(7):  # Days 0-6 (Monday-Sunday)
        day_data = []
        for hour in range(24):
            day_data.append(0)
        heatmap_matrix.append(day_data)
    
    # Fill the matrix with data
    day_names = list(calendar.day_name)
    for day, hour, avg_count in heatmap_data:
        day_idx = int(day)
        hour_idx = int(hour)
        # Handle day of week format differences 
        # Adjust based on your database's DOW representation
        # PostgreSQL: 0=Sunday, 1=Monday, ..., 6=Saturday
        # We'll standardize to 0=Monday, ..., 6=Sunday for the response
        adjusted_day = (day_idx + 6) % 7
        heatmap_matrix[adjusted_day][hour_idx] = round(float(avg_count), 1) if avg_count else 0
    
    # Format data for the response
    formatted_data = []
    for day_idx, day_data in enumerate(heatmap_matrix):
        day_name = day_names[day_idx]
        for hour_idx, value in enumerate(day_data):
            formatted_data.append({
                "day": day_idx,
                "day_name": day_name,
                "hour": hour_idx,
                "hour_formatted": f"{hour_idx}:00",
                "value": value
            })
    
    # Calculate overall busiest times
    busiest_times = sorted(formatted_data, key=lambda x: x["value"], reverse=True)[:5]
    
    # Get camera list for reference
    camera_list = get_camera_list(db)
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days_analyzed": days,
        "camera_id": camera_id,
        "heatmap_data": formatted_data,
        "busiest_times": busiest_times,
        "cameras": camera_list,
        "days": [{"index": i, "name": name} for i, name in enumerate(day_names)],
        "hours": [{"hour": h, "formatted": f"{h}:00"} for h in range(24)]
    }

@router.post("/process-video-for-trends/", response_model=Dict)
async def process_video_for_trends(
    background_tasks: BackgroundTasks,
    camera_id: str,
    video_path: str,
    date_recorded: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Process a video file specifically for visitor trend analysis
    
    - Processes video through detection pipeline
    - Specifies the camera ID for accurate trend mapping
    - Can process historical video by specifying recording date
    """
    # Validate video path exists
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"Video file not found at: {video_path}")
    
    # Get recording date (defaults to today)
    if date_recorded:
        try:
            recording_date = datetime.strptime(date_recorded, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        recording_date = datetime.now().date()
    
    # Add video processing task to background tasks
    job_id = f"trend_analysis_{camera_id}_{int(datetime.now().timestamp())}"
    
    # Add to background tasks
    background_tasks.add_task(
        process_video_file,
        file_path=video_path,
        job_id=job_id,
        db=db,
        camera_id=camera_id,
        recording_date=recording_date
    )
    
    return {
        "job_id": job_id, 
        "status": "Processing started",
        "camera_id": camera_id,
        "date_recorded": recording_date.isoformat(),
        "message": "Video is being processed for visitor trend analysis"
    }

@router.get("/camera-zones/", response_model=Dict)
async def get_camera_zones(db: Session = Depends(get_db)):
    """
    Get all camera zones (locations) available in the system
    
    - Returns a list of all cameras that have provided data
    - Includes zone information if available
    """
    # Get distinct camera IDs from detection events
    camera_list = get_camera_list(db)
    
    return {
        "cameras": camera_list,
        "total_cameras": len(camera_list)
    }

# Helper functions for data processing
def process_hourly_trends(detection_data, start_datetime, end_datetime):
    """Process hourly visitor trends from detection data"""
    hourly_trends = {}
    camera_hourly_counts = {}
    
    # Initialize with zero values for all hours in the range
    current_dt = start_datetime
    while current_dt <= end_datetime:
        hour_key = current_dt.strftime("%Y-%m-%d %H:00")
        hourly_trends[hour_key] = {
            "timestamp": hour_key,
            "total_visitors": 0,
            "hour": current_dt.hour,
            "date": current_dt.strftime("%Y-%m-%d"),
            "camera_counts": {}
        }
        current_dt += timedelta(hours=1)
    
    # Group detections by hour and camera
    for entry in detection_data:
        hour_key = entry.timestamp.strftime("%Y-%m-%d %H:00")
        camera_id = entry.camera_id
        person_count = entry.person_count or 0
        
        if hour_key not in camera_hourly_counts:
            camera_hourly_counts[hour_key] = {}
            
        if camera_id not in camera_hourly_counts[hour_key]:
            camera_hourly_counts[hour_key][camera_id] = {
                "sum": 0,
                "count": 0
            }
            
        # Accumulate values for this camera in this hour
        camera_hourly_counts[hour_key][camera_id]["sum"] += person_count
        camera_hourly_counts[hour_key][camera_id]["count"] += 1
    
    # Calculate average for each camera in each hour
    for hour_key, cameras in camera_hourly_counts.items():
        if hour_key in hourly_trends:
            hourly_trend = hourly_trends[hour_key]
            total_visitors = 0
            
            for camera_id, data in cameras.items():
                # Calculate average for this camera
                avg_count = data["sum"] / data["count"] if data["count"] > 0 else 0
                
                # Add to camera-specific counts
                hourly_trend["camera_counts"][camera_id] = round(avg_count, 1)
                
                # Add to total
                total_visitors += avg_count
                
            # Update total visitors (sum of camera averages)
            hourly_trend["total_visitors"] = round(total_visitors, 1)
    
    # Convert to list and sort by timestamp
    return sorted(hourly_trends.values(), key=lambda x: x["timestamp"])

def process_daily_trends(detection_data, start_date, end_date):
    """Process daily visitor trends from detection data"""
    daily_trends = {}
    daily_camera_data = {}
    
    # Initialize for all days in range
    current_date = start_date
    while current_date <= end_date:
        day_key = current_date.strftime("%Y-%m-%d")
        daily_trends[day_key] = {
            "date": day_key,
            "total_visitors": 0,
            "camera_counts": {},
            "day_of_week": calendar.day_name[current_date.weekday()]
        }
        current_date += timedelta(days=1)
    
    # Group by day and camera
    for entry in detection_data:
        day_key = entry.timestamp.strftime("%Y-%m-%d")
        camera_id = entry.camera_id
        person_count = entry.person_count or 0
        
        if day_key not in daily_camera_data:
            daily_camera_data[day_key] = {}
            
        if camera_id not in daily_camera_data[day_key]:
            daily_camera_data[day_key][camera_id] = {
                "sum": 0,
                "count": 0
            }
        
        # Accumulate values
        daily_camera_data[day_key][camera_id]["sum"] += person_count
        daily_camera_data[day_key][camera_id]["count"] += 1
    
    # Calculate daily averages for each camera
    for day_key, cameras in daily_camera_data.items():
        if day_key in daily_trends:
            daily_trend = daily_trends[day_key]
            total_daily_visitors = 0
            
            for camera_id, data in cameras.items():
                # Calculate average for this camera
                avg_count = data["sum"] / data["count"] if data["count"] > 0 else 0
                
                # Store in results
                daily_trend["camera_counts"][camera_id] = round(avg_count, 1)
                
                # Add to total
                total_daily_visitors += avg_count
            
            # Update total (sum of camera averages)
            daily_trend["total_visitors"] = round(total_daily_visitors, 1)
    
    # Convert to list and sort by date
    return sorted(daily_trends.values(), key=lambda x: x["date"])

def process_weekly_trends(detection_data, start_date, end_date):
    """Process weekly visitor trends from detection data"""
    weekly_trends = {}
    weekly_camera_data = {}
    
    # Group by ISO week
    for entry in detection_data:
        year, week, _ = entry.timestamp.isocalendar()
        week_key = f"{year}-W{week:02d}"
        camera_id = entry.camera_id
        person_count = entry.person_count or 0
        
        # Initialize structures if needed
        if week_key not in weekly_camera_data:
            weekly_camera_data[week_key] = {}
            
        if camera_id not in weekly_camera_data[week_key]:
            weekly_camera_data[week_key][camera_id] = {
                "sum": 0,
                "count": 0
            }
            
        # Accumulate values
        weekly_camera_data[week_key][camera_id]["sum"] += person_count
        weekly_camera_data[week_key][camera_id]["count"] += 1
        
        # Initialize weekly trend data structure
        if week_key not in weekly_trends:
            weekly_trends[week_key] = {
                "week": week_key,
                "year": year,
                "week_number": week,
                "total_visitors": 0,
                "camera_counts": {}
            }
    
    # Calculate weekly averages
    for week_key, cameras in weekly_camera_data.items():
        weekly_trend = weekly_trends[week_key]
        total_weekly_visitors = 0
        
        for camera_id, data in cameras.items():
            # Calculate average for this camera
            avg_count = data["sum"] / data["count"] if data["count"] > 0 else 0
            
            # Store in results
            weekly_trend["camera_counts"][camera_id] = round(avg_count, 1)
            
            # Add to total
            total_weekly_visitors += avg_count
        
        # Update total (sum of camera averages)
        weekly_trend["total_visitors"] = round(total_weekly_visitors, 1)
    
    # Convert to list and sort by week
    return sorted(weekly_trends.values(), key=lambda x: (x["year"], x["week_number"]))

def get_camera_list(db: Session) -> List[Dict[str, Any]]:
    """Get a list of all cameras in the system with metadata"""
    # Query distinct camera IDs
    cameras = db.query(
        DetectionEvent.camera_id, 
        func.min(DetectionEvent.timestamp).label('first_seen'),
        func.max(DetectionEvent.timestamp).label('last_seen'),
        func.count(distinct(func.date(DetectionEvent.timestamp))).label('days_active')
    ).group_by(
        DetectionEvent.camera_id
    ).all()
    
    # Format camera data
    camera_list = []
    for camera_id, first_seen, last_seen, days_active in cameras:
        # Skip empty camera IDs
        if not camera_id:
            continue
            
        camera_list.append({
            "camera_id": camera_id,
            "first_seen": first_seen.isoformat() if first_seen else None,
            "last_seen": last_seen.isoformat() if last_seen else None,
            "days_active": days_active or 0,
            # Default zone name based on camera ID
            "zone_name": f"Zone {camera_id.split('_')[-1]}" if camera_id else "Unknown Zone"
        })
    
    return camera_list