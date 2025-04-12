from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import tempfile
from datetime import datetime, timedelta
import os
import boto3
from urllib.parse import urlparse

from app.core.database import get_db
from app.schemas.alert import Alert, AlertCreate, AlertUpdate
from app.models.alert import Alert as AlertModel
from app.core.config import settings

router = APIRouter()
connected_clients = set()

@router.get("/", response_model=List[Alert])
async def get_alerts(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    alert_type: Optional[str] = None,
    severity: Optional[int] = None,
    acknowledged: Optional[bool] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get alerts with optional filtering
    """
    query = db.query(AlertModel)
    
    if start_time:
        query = query.filter(AlertModel.timestamp >= start_time)
    if end_time:
        query = query.filter(AlertModel.timestamp <= end_time)
    if alert_type:
        query = query.filter(AlertModel.alert_type == alert_type)
    if severity is not None:
        query = query.filter(AlertModel.severity >= severity)
    if acknowledged is not None:
        query = query.filter(AlertModel.acknowledged == acknowledged)
    
    query = query.order_by(AlertModel.timestamp.desc())
    if limit is not None:
        query = query.limit(limit)
        
    alerts = query.all()
    return alerts

@router.put("/{alert_id}", response_model=Alert)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db)
):
    """
    Update alert status (e.g., acknowledge alert)
    """
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Update alert fields
    if alert_update.acknowledged is not None:
        alert.acknowledged = alert_update.acknowledged
        if alert_update.acknowledged:
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = alert_update.acknowledged_by
    
    db.commit()
    db.refresh(alert)
    return alert

@router.get("/snapshot/{alert_id}", response_class=FileResponse)
async def get_alert_snapshot(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the snapshot image for a specific alert
    """
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    if not alert.snapshot_path:
        raise HTTPException(status_code=404, detail="No snapshot available for this alert")
    
    try:
        # If it's an S3 URL, return a redirect to the URL
        if alert.snapshot_path.startswith('http'):
            return RedirectResponse(url=alert.snapshot_path)
            
        # For legacy local files
        if os.path.isabs(alert.snapshot_path):
            full_path = alert.snapshot_path
        else:
            if not os.path.isfile(alert.snapshot_path):
                full_path = os.path.join(settings.SNAPSHOT_BASE_DIR, alert.snapshot_path)
            else:
                full_path = alert.snapshot_path
                
        # Check if file exists
        if not os.path.exists(full_path):
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Snapshot file not found for alert_id {alert_id}. Path tried: {full_path}")
            # Try to find the thumbnail version as a fallback
            thumb_path = os.path.splitext(full_path)[0] + "_thumb.jpg"
            if os.path.exists(thumb_path):
                return FileResponse(thumb_path, media_type="image/jpeg")
            raise HTTPException(status_code=404, detail=f"Snapshot file not found: {full_path}")
            
        return FileResponse(full_path, media_type="image/jpeg")
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error retrieving snapshot for alert_id {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving snapshot: {str(e)}")

@router.get("/stats/", response_model=dict)
async def get_alert_stats(
    days: int = Query(7, description="Number of days to include in stats"),
    db: Session = Depends(get_db)
):
    """
    Get alert statistics for the dashboard
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get total counts by type
    query = db.query(
        AlertModel.alert_type,
        db.func.count(AlertModel.id)
    ).filter(
        AlertModel.timestamp >= start_date,
        AlertModel.timestamp <= end_date
    ).group_by(
        AlertModel.alert_type
    )
    
    type_counts = dict(query.all())
    
    # Get counts by severity
    query = db.query(
        AlertModel.severity,
        db.func.count(AlertModel.id)
    ).filter(
        AlertModel.timestamp >= start_date,
        AlertModel.timestamp <= end_date
    ).group_by(
        AlertModel.severity
    )
    
    severity_counts = dict(query.all())
    
    # Get daily counts
    daily_query = db.query(
        db.func.date_trunc('day', AlertModel.timestamp).label('day'),
        db.func.count(AlertModel.id)
    ).filter(
        AlertModel.timestamp >= start_date,
        AlertModel.timestamp <= end_date
    ).group_by('day').order_by('day')
    
    daily_counts = [
        {"date": day.strftime("%Y-%m-%d"), "count": count}
        for day, count in daily_query.all()
    ]
    
    return {
        "by_type": type_counts,
        "by_severity": severity_counts,
        "daily_counts": daily_counts,
        "total": sum(type_counts.values())
    }

@router.websocket("/ws")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alerts
    """
    await websocket.accept()
    connected_clients.add(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

@router.post("/{alert_id}/acknowledge", response_model=Alert)
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Acknowledge a specific alert
    """
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledged = True
    alert.acknowledged_at = datetime.now()
    
    db.commit()
    db.refresh(alert)
    return alert

async def download_from_s3(s3_uri: str) -> str:
    """Download a file from S3 to a temporary location and return the path"""
    try:
        parsed = urlparse(s3_uri)
        bucket_name = parsed.netloc
        s3_key = parsed.path.lstrip('/')
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        s3_client.download_file(bucket_name, s3_key, temp_file.name)
        
        return temp_file.name
    except Exception as e:
        logger.error(f"Error downloading from S3: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve snapshot from S3")