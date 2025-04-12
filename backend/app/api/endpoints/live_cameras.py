# app/api/endpoints/live_cameras.py
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks, WebSocket, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import time
from datetime import datetime, timedelta
import cv2
import io
import asyncio
import logging
import numpy as np
from app.core.database import get_db
from app.services.live_camera import live_camera_processor
from app.models.detection import DetectionEvent
from pydantic import BaseModel
from app.models.camera import Camera as CameraModel
from app.utils.rtsp_tester import test_rtsp_connection, fix_rtsp_url

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

class CameraSource(BaseModel):
    camera_id: str
    source: str
    zone_name: Optional[str] = None

class CameraAction(BaseModel):
    camera_id: str

class RTSPDiagnostic(BaseModel):
    url: str
    timeout: int = 10

@router.post("/register/", response_model=Dict)
async def register_camera(camera: CameraSource, db: Session = Depends(get_db)):
    """
    Register a new camera for streaming and processing
    
    - Camera ID should be unique
    - Source can be a file path, RTSP URL, or device ID
    - Zone name is optional for identifying the camera location
    """
    # First check if the camera already exists in the database
    existing_camera = db.query(CameraModel).filter(CameraModel.name == camera.camera_id).first()
    
    if existing_camera:
        # If camera exists in database but is marked as inactive, reactivate it
        existing_camera.is_active = True
        existing_camera.last_active = datetime.now()
        existing_camera.rtsp_url = camera.source
        existing_camera.zones = {"default": camera.zone_name or f"Zone {camera.camera_id}"}
        db.commit()
        
        # Add to live_camera_processor if not already there
        if camera.camera_id not in live_camera_processor.cameras:
            success = live_camera_processor.add_camera(
                camera_id=camera.camera_id,
                source=camera.source,
                zone_name=camera.zone_name
            )
            
            if not success:
                raise HTTPException(status_code=400, detail=f"Failed to register camera {camera.camera_id}")
        
        return {
            "camera_id": camera.camera_id,
            "status": "reactivated",
            "message": f"Camera {camera.camera_id} reactivated successfully"
        }
    else:
        # Register new camera
        success = live_camera_processor.add_camera(
            camera_id=camera.camera_id,
            source=camera.source,
            zone_name=camera.zone_name
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to register camera {camera.camera_id}")
        
        return {
            "camera_id": camera.camera_id,
            "status": "registered",
            "message": f"Camera {camera.camera_id} registered successfully"
        }

@router.post("/start/", response_model=Dict)
async def start_camera(camera: CameraAction):
    """
    Start processing a registered camera
    """
    success = live_camera_processor.start_camera(camera.camera_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to start camera {camera.camera_id}")
    
    return {
        "camera_id": camera.camera_id,
        "status": "started",
        "message": f"Camera {camera.camera_id} started successfully"
    }

@router.post("/stop/", response_model=Dict)
async def stop_camera(camera: CameraAction):
    """
    Stop processing a camera
    """
    success = live_camera_processor.stop_camera(camera.camera_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to stop camera {camera.camera_id}")
    
    return {
        "camera_id": camera.camera_id,
        "status": "stopped",
        "message": f"Camera {camera.camera_id} stopped successfully"
    }

@router.get("/status/", response_model=Dict)
async def get_camera_status(camera_id: Optional[str] = None):
    """
    Get status of a specific camera or all cameras
    """
    return live_camera_processor.get_camera_status(camera_id)

@router.get("/frame/{camera_id}", response_class=Response)
async def get_camera_frame(camera_id: str):
    """
    Get the latest frame from a camera as JPEG image
    """
    frame_bytes, timestamp = live_camera_processor.get_latest_frame_jpg(camera_id)
    
    if frame_bytes is None:
        raise HTTPException(status_code=404, detail=f"No frame available for camera {camera_id}")
    
    return Response(content=frame_bytes, media_type="image/jpeg")

@router.get("/stream/{camera_id}")
async def stream_camera(camera_id: str):
    """
    Stream the camera feed as multipart/x-mixed-replace
    """
    if camera_id not in live_camera_processor.cameras:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")
    
    return StreamingResponse(
        stream_generator(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

async def stream_generator(camera_id: str):
    """
    Generator function for video streaming with optimizations for high-resolution content
    """
    # Adaptive frame rate based on the camera resolution
    camera_status = live_camera_processor.get_camera_status(camera_id)
    
    # Default frame interval (10 FPS)
    frame_interval = 0.1
    
    # Track how many frames we've processed
    frame_count = 0
    
    # If this is a high-resolution camera, reduce the frame rate
    original_width = camera_status.get("original_width", 0)
    original_height = camera_status.get("original_height", 0)
    if original_width > 0 and original_height > 0:
        # For high-resolution cameras, use a lower frame rate
        if original_width * original_height > 1920 * 1080:
            frame_interval = 0.2  # 5 FPS for high-res
            logger.info(f"Using reduced frame rate for high-res camera {camera_id}: 5 FPS")
    
    while camera_id in live_camera_processor.cameras:
        frame_count += 1
        
        # Check if camera is running
        status = live_camera_processor.get_camera_status(camera_id)
        if status.get("status") != "running":
            # If camera is not running but exists, yield a placeholder frame
            placeholder = create_placeholder_frame(camera_id, status.get("status", "unknown"))
            _, buffer = cv2.imencode('.jpg', placeholder)
            frame_bytes = buffer.tobytes()
        else:
            # Get the latest frame
            frame_bytes, _ = live_camera_processor.get_latest_frame_jpg(camera_id)
            
            if frame_bytes is None:
                # If no frame is available, yield a placeholder
                placeholder = create_placeholder_frame(camera_id, "no frame")
                _, buffer = cv2.imencode('.jpg', placeholder)
                frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Log stream performance occasionally
        if frame_count % 50 == 0:
            logger.debug(f"Camera {camera_id} streaming: delivered {frame_count} frames")
        
        # Control frame rate of the stream with adaptive interval
        await asyncio.sleep(frame_interval)

@router.post("/start-all/", response_model=Dict)
async def start_all_cameras():
    """
    Start processing all registered cameras
    """
    results = live_camera_processor.start_all_cameras()
    success_count = sum(1 for success in results.values() if success)
    
    return {
        "message": f"Started {success_count} of {len(results)} cameras",
        "details": results
    }

@router.post("/stop-all/", response_model=Dict)
async def stop_all_cameras():
    """
    Stop processing all cameras
    """
    results = live_camera_processor.stop_all_cameras()
    success_count = sum(1 for success in results.values() if success)
    
    return {
        "message": f"Stopped {success_count} of {len(results)} cameras",
        "details": results
    }

@router.get("/analytics/{camera_id}", response_model=Dict)
async def get_camera_analytics(
    camera_id: str,
    hours: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get analytics for a specific camera over the last N hours
    """
    # Calculate time range
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Query detection events
    events = db.query(DetectionEvent).filter(
        DetectionEvent.camera_id == camera_id,
        DetectionEvent.timestamp >= start_time,
        DetectionEvent.timestamp <= end_time
    ).order_by(DetectionEvent.timestamp).all()
    
    # Calculate metrics
    total_detections = len(events)
    
    if total_detections == 0:
        return {
            "camera_id": camera_id,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            },
            "metrics": {
                "total_detections": 0,
                "average_person_count": 0,
                "max_person_count": 0
            },
            "message": "No detection events in the selected time range"
        }
    
    # Calculate analytics
    avg_person_count = sum(event.person_count or 0 for event in events) / total_detections
    max_person_count = max((event.person_count or 0) for event in events)
    
    # Group by minute for time-series data
    time_series = {}
    for event in events:
        minute_key = event.timestamp.strftime("%Y-%m-%d %H:%M")
        if minute_key not in time_series:
            time_series[minute_key] = {
                "timestamp": minute_key,
                "person_count": 0,
                "count": 0
            }
        
        time_series[minute_key]["person_count"] += event.person_count or 0
        time_series[minute_key]["count"] += 1
    
    # Calculate average per minute
    for key in time_series:
        if time_series[key]["count"] > 0:
            time_series[key]["person_count"] = time_series[key]["person_count"] / time_series[key]["count"]
        del time_series[key]["count"]
    
    return {
        "camera_id": camera_id,
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "hours": hours
        },
        "metrics": {
            "total_detections": total_detections,
            "average_person_count": round(avg_person_count, 2),
            "max_person_count": max_person_count
        },
        "time_series": list(time_series.values())
    }

@router.post("/diagnose-rtsp/", response_model=Dict)
async def diagnose_rtsp_connection(diagnostic: RTSPDiagnostic):
    """
    Test RTSP connection and provide detailed diagnostics
    
    This endpoint helps troubleshoot issues with RTSP cameras by testing:
    - Network connectivity to the camera
    - Authentication issues
    - Stream format support
    - Frame decoding
    """
    try:
        # First try to fix any common issues with the URL format
        fixed_url = fix_rtsp_url(diagnostic.url)
        if fixed_url != diagnostic.url:
            logger.info(f"Fixed RTSP URL from {diagnostic.url} to {fixed_url}")
        
        # Run the test
        results = test_rtsp_connection(fixed_url, diagnostic.timeout)
        
        # Add helpful metadata
        results["url_fixed"] = fixed_url != diagnostic.url
        if results["url_fixed"]:
            results["original_url"] = diagnostic.url
            results["fixed_url"] = fixed_url
        
        # Add timestamp
        results["timestamp"] = datetime.now().isoformat()
        
        return results
    except Exception as e:
        logger.error(f"Error during RTSP diagnostics: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.websocket("/websocket/{camera_id}")
async def websocket_endpoint(websocket: WebSocket, camera_id: str):
    """
    WebSocket endpoint for streaming camera frames
    """
    await websocket.accept()
    
    if camera_id not in live_camera_processor.cameras:
        await websocket.send_json({"error": f"Camera {camera_id} not found"})
        await websocket.close()
        return
    
    # Start the camera if it's not already running
    if live_camera_processor.get_camera_status(camera_id).get("status") != "running":
        live_camera_processor.start_camera(camera_id)
    
    try:
        # Keep sending frames until the connection is closed
        while True:
            # Get the latest frame
            frame_bytes, _ = live_camera_processor.get_latest_frame_jpg(camera_id)
            
            if frame_bytes is None:
                # If no frame is available, create a placeholder
                placeholder = create_placeholder_frame(camera_id, "no frame")
                _, buffer = cv2.imencode('.jpg', placeholder)
                frame_bytes = buffer.tobytes()
            
            # Send the frame as binary
            await websocket.send_bytes(frame_bytes)
            
            # Wait a bit before sending the next frame
            await asyncio.sleep(0.1)
    
    except Exception as e:
        logger.error(f"WebSocket error for camera {camera_id}: {str(e)}")
    
    finally:
        # Close the WebSocket connection
        await websocket.close()

def create_placeholder_frame(camera_id: str, status: str):
    """
    Create a placeholder frame for cameras that are not running
    """
    # Create a black frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add text
    cv2.putText(
        frame,
        f"Camera {camera_id}",
        (50, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )
    
    cv2.putText(
        frame,
        f"Status: {status}",
        (50, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )
    
    cv2.putText(
        frame,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        (50, 300),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )
    
    return frame