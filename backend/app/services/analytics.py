from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from collections import defaultdict

from app.models.analytics import Analytics

def get_zone_dwell_times(
    db: Session,
    camera_id: int,
    zone_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Analyze dwell times in specific camera zones.
    
    Args:
        camera_id: ID of the camera to analyze
        zone_name: Optional specific zone to analyze. If None, analyzes all zones
        start_date: Optional start date for analysis
        end_date: Optional end date for analysis
    """
    # Build query
    query = db.query(Analytics).filter(Analytics.camera_id == camera_id)
    
    if start_date:
        query = query.filter(Analytics.timestamp >= start_date)
    if end_date:
        query = query.filter(Analytics.timestamp <= end_date)
    
    analytics_data = query.all()
    
    # Initialize results
    zone_dwell_times = defaultdict(list)
    hourly_dwell_times = defaultdict(lambda: defaultdict(list))
    
    # Process each analytics entry
    for entry in analytics_data:
        if not entry.dwell_times:
            continue
            
        for zone, dwell_time in entry.dwell_times.items():
            # If specific zone requested, only process that zone
            if zone_name and zone != zone_name:
                continue
                
            zone_dwell_times[zone].append(dwell_time)
            
            # Track dwell times by hour
            hour = entry.timestamp.hour
            hourly_dwell_times[zone][f"{hour:02d}:00"].append(dwell_time)
    
    # Calculate statistics
    results = {}
    for zone, times in zone_dwell_times.items():
        if not times:
            continue
            
        # Calculate basic statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        # Calculate hourly averages
        hourly_avgs = {
            hour: sum(times) / len(times) if times else 0
            for hour, times in hourly_dwell_times[zone].items()
        }
        
        # Find peak hours (top 3 hours with longest dwell times)
        peak_hours = dict(sorted(
            hourly_avgs.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3])
        
        results[zone] = {
            "average_dwell_time": avg_time,
            "min_dwell_time": min_time,
            "max_dwell_time": max_time,
            "total_observations": len(times),
            "peak_hours": peak_hours,
            "hourly_averages": hourly_avgs
        }
    
    return results

def calculate_daily_summary(db: Session, date: str) -> Dict[str, Any]:
    """
    Calculate daily summary of traffic analytics including:
    - Entry/exit counts
    - Peak hours
    - Zone occupancy
    - Dwell times
    - Movement patterns
    """
    start_date = datetime.strptime(date, "%Y-%m-%d")
    end_date = start_date + timedelta(days=1)
    
    # Query all analytics data for the specified date
    analytics_data = db.query(Analytics).filter(
        Analytics.timestamp >= start_date,
        Analytics.timestamp < end_date
    ).all()
    
    # Initialize summary data
    total_entries = 0
    total_exits = 0
    hourly_distribution = defaultdict(int)
    zone_occupancy = defaultdict(int)
    dwell_times = defaultdict(list)
    movement_heatmap = defaultdict(lambda: defaultdict(int))
    
    # Process each analytics entry
    for entry in analytics_data:
        if entry.entry_count is not None:
            total_entries += entry.entry_count
        if entry.exit_count is not None:
            total_exits += entry.exit_count
        
        # Calculate hourly distribution
        hour = entry.timestamp.hour
        hourly_distribution[f"{hour:02d}:00"] += entry.total_people
        
        # Calculate zone occupancy
        if entry.people_per_zone:
            for zone, count in entry.people_per_zone.items():
                zone_occupancy[zone] += count
        
        # Calculate dwell times
        if entry.dwell_times:
            for zone, time in entry.dwell_times.items():
                dwell_times[zone].append(time)
        
        # Calculate movement patterns
        if entry.movement_patterns:
            for from_zone, movements in entry.movement_patterns.items():
                for movement in movements:
                    to_zone = movement.get("to_zone")
                    if to_zone:
                        movement_heatmap[from_zone][to_zone] += 1
    
    # Calculate average dwell times
    average_dwell_times = {
        zone: sum(times) / len(times) if times else 0
        for zone, times in dwell_times.items()
    }
    
    # Find busiest zones
    busiest_zones = [
        {"zone": zone, "occupancy": count}
        for zone, count in sorted(
            zone_occupancy.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5 busiest zones
    ]
    
    # Find peak hours (top 3 hours with most traffic)
    peak_hours = dict(sorted(
        hourly_distribution.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3])
    
    return {
        "date": date,
        "total_entries": total_entries,
        "total_exits": total_exits,
        "peak_hours": peak_hours,
        "zone_occupancy": dict(zone_occupancy),
        "average_dwell_times": average_dwell_times,
        "busiest_zones": busiest_zones,
        "movement_heatmap": {
            from_zone: dict(to_zones)
            for from_zone, to_zones in movement_heatmap.items()
        }
    } 