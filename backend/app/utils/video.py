# app/utils/video.py (simplified)
import cv2
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session

from app.services.detector import DetectionService
from app.services.tracker import PersonTracker
from app.services.behavior import BehaviorAnalysisService
from app.models.detection import DetectionEvent
from app.models.alert import Alert
from app.models.analytics import Analytics
from app.core.config import settings

logger = logging.getLogger(__name__)

def process_video_file(file_path: str, job_id: str, db: Session, camera_id: str = "cam_001", recording_date: datetime = None):
    """
    Process a video file for security analysis
    
    Args:
        file_path: Path to the video file
        job_id: Unique job identifier
        db: Database session
        camera_id: Optional camera identifier (defaults to cam_001)
        recording_date: Optional date when the video was recorded
    """
    try:
        # Initialize services
        detector = DetectionService(conf_threshold=settings.DETECTION_CONFIDENCE_THRESHOLD)
        tracker = PersonTracker(iou_threshold=settings.TRACKING_IOU_THRESHOLD)
        behavior_analyzer = BehaviorAnalysisService()
        
        # Open video file with improved buffer settings
        cap = cv2.VideoCapture(file_path)
        
        # Set buffer size to better handle HEVC streams
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 5)
        
        # Try to enable hardware acceleration if available
        cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
        
        if not cap.isOpened():
            logger.error(f"Error opening video file: {file_path}")
            return
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Log video properties
        logger.info(f"Processing video: {file_path}, Resolution: {width}x{height}, FPS: {fps}, Duration: {duration}s")
        
        # Configure target processing resolution (much lower than input if high-res)
        target_width = 640
        target_height = 360
        
        # Determine if downsampling is needed (for high-resolution videos)
        downsampling_needed = width > 1280 or height > 720
        
        # Dynamically set skip factor based on resolution
        if width * height > 1920 * 1080:
            # For very high resolution videos, process fewer frames
            skip_factor = max(5, min(15, int((width * height) / (640 * 360) / 3)))
        else:
            # For lower resolutions, process more frames
            skip_factor = 5
            
        logger.info(f"Using frame skip factor: {skip_factor} (processing every {skip_factor}th frame)")
        
        # Process frames
        frame_number = 0
        processing_start = time.time()
        last_processing_time = 0
        total_processing_time = 0
        
        # Initialize statistics counters
        total_alerts = 0
        processed_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_number += 1
            timestamp = frame_number / fps
            
            # Process every N frames for efficiency
            if frame_number % skip_factor != 0 and frame_number != 1:
                continue
                
            # Downsample frame if needed
            if downsampling_needed:
                frame = cv2.resize(frame, (target_width, target_height))
            
            # Track processing time for this frame
            frame_start_time = time.time()
            
            # Detect persons
            detections = detector.detect_persons(frame)
            
            # Classify persons (staff vs customer, gender)
            detections = detector.classify_persons(frame, detections)
            
            # Track persons
            tracked_persons = tracker.update(detections, frame)
            
            # Analyze behavior
            analytics_data, alerts = behavior_analyzer.analyze_frame(frame, tracked_persons, timestamp)
            
            # Store detection event in database
            detection_event = DetectionEvent(
                timestamp=datetime.now() if not recording_date else 
                           datetime.combine(recording_date, datetime.now().time()),
                camera_id=camera_id,  # Use provided camera ID
                frame_number=frame_number,
                person_count=len(tracked_persons),
                x=0.0,  # Default x coordinate (center of frame)
                y=0.0,  # Default y coordinate (center of frame)
                confidence=1.0,  # Default confidence
                detection_data={
                    "persons": [
                        {
                            "track_id": p.get("track_id"),
                            "bbox": p.get("bbox"),
                            "is_staff": p.get("is_staff", False),
                            "gender": p.get("gender", "unknown")
                        } for p in tracked_persons
                    ]
                }
            )
            db.add(detection_event)
            
            # Store alerts in database
            for alert_data in alerts:
                alert = Alert(
                    timestamp=datetime.fromisoformat(alert_data["timestamp"]),
                    alert_type=alert_data["alert_type"],
                    severity=alert_data["severity"],
                    track_id=alert_data["track_id"],
                    description=alert_data["description"],
                    snapshot_path=alert_data.get("snapshot_path")
                )
                db.add(alert)
                total_alerts += 1
            
            # Store analytics in database
            for analytics in analytics_data:
                analytics_entry = Analytics(
                    timestamp=datetime.fromisoformat(analytics["timestamp"]),
                    person_count=analytics["person_count"],
                    staff_count=analytics["staff_count"],
                    customer_count=analytics["customer_count"],
                    suspicious_activity_count=analytics["suspicious_activity_count"]
                )
                db.add(analytics_entry)
            
            # Calculate frame processing time
            frame_processing_time = time.time() - frame_start_time
            last_processing_time = frame_processing_time
            total_processing_time += frame_processing_time
            processed_frames += 1
            
            # Commit to database every 100 frames
            if frame_number % 100 == 0:
                db.commit()
                
                # Log progress
                progress = (frame_number / frame_count) * 100 if frame_count > 0 else 0
                elapsed = time.time() - processing_start
                remaining = (elapsed / frame_number) * (frame_count - frame_number) if frame_number > 0 else 0
                avg_processing_time = total_processing_time / processed_frames if processed_frames > 0 else 0
                
                logger.info(f"Processing progress: {progress:.1f}%, ETA: {remaining:.1f}s, Avg. frame time: {avg_processing_time:.3f}s")
        
        # Final commit
        db.commit()
        
        # Cleanup
        cap.release()
        if os.path.exists(file_path) and file_path.startswith("/tmp/"):
            os.remove(file_path)
        
        processing_time = time.time() - processing_start
        logger.info(f"Video processing complete. Processed {processed_frames}/{frame_number} frames in {processing_time:.2f}s")
        logger.info(f"Generated {total_alerts} alerts")
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        # Attempt to clean up
        if 'cap' in locals():
            cap.release()
        if os.path.exists(file_path) and file_path.startswith("/tmp/"):
            os.remove(file_path)
        db.rollback()
        raise