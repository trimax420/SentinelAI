import cv2
import threading
import time
import logging
import queue
import os
import numpy as np
import asyncio
from datetime import datetime, timedelta, time as dt_time
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Tuple
from app.core.database import SessionLocal
from app.services.detector import DetectionService
from app.services.tracker import PersonTracker
from app.services.behavior import BehaviorAnalysisService
from app.models.detection import DetectionEvent
from app.models.alert import Alert
from app.models.analytics import Analytics, HourlyFootfall, HourlyDemographics
from app.services.suspect_tracking import SuspectTrackingService
from collections import defaultdict
import logging
from sqlalchemy import insert
# Import our new HEVC stream handler
from app.utils.hevc_stream import create_stream_handler, is_hevc_stream
# Import our new RTSP tester
from app.utils.rtsp_tester import test_rtsp_connection, fix_rtsp_url

logger = logging.getLogger(__name__)
try:
    from deepface import DeepFace
    deepface_available = True
except ImportError:
    logger.warning("DeepFace library not found. Demographics analysis will be disabled.")
    deepface_available = False

logger = logging.getLogger(__name__)

class LiveCameraProcessor:
    """
    Service for processing multiple camera feeds simultaneously
    with real-time processing and analytics
    """
    
    def __init__(self):
        self.cameras: Dict[str, Dict] = {}
        self.processing_threads: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, bool] = {}
        self.frame_queues: Dict[str, queue.Queue] = {}
        self.latest_frames: Dict[str, Tuple[np.ndarray, datetime]] = {}
        self.detector = DetectionService()
        self.tracker = PersonTracker()
        self.behavior_analyzer = BehaviorAnalysisService()
        self.suspect_tracking_service = SuspectTrackingService()
        
        # Create directory for saving frames if it doesn't exist
        self.frames_dir = "data/live_frames"
        os.makedirs(self.frames_dir, exist_ok=True)
        
        # Load existing active cameras from database
        self._load_cameras_from_database()
        
        # Optional: Auto-start cameras that were recently active
        self._auto_restart_active_cameras()
        
        self.hourly_footfall_tracker = defaultdict(lambda: defaultdict(set))
        self.hourly_demographics_tracker = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        self.last_aggregation_time = time.time()
        self.aggregation_interval = 300 # Aggregate/Store every 5 minutes

        # Placeholder for actual demographics model/function
        self.demographics_estimator = self._initialize_demographics_estimator() 
        
        logger.info("Live camera processor initialized")
    
    def _load_cameras_from_database(self):
        """
        Load existing active cameras from the database when the service starts
        """
        db = SessionLocal()
        try:
            from app.models.camera import Camera
            # Get all active cameras
            active_cameras = db.query(Camera).filter(Camera.is_active == True).all()
            logger.info(f"Found {len(active_cameras)} active cameras in database")
            
            for camera_db in active_cameras:
                camera_id = camera_db.name
                source = camera_db.rtsp_url
                zone_name = camera_db.zones.get("default") if camera_db.zones else None
                
                logger.info(f"Loading camera {camera_id} from database")
                # Add to memory but don't add to database again
                self.cameras[camera_id] = {
                    "source": source,
                    "zone_name": zone_name or f"Zone {camera_id}",
                    "status": "ready",
                    "last_error": None,
                    "started_at": None,
                    "frames_processed": 0,
                    "persons_detected": 0
                }
                
                # Initialize frame queue for this camera
                self.frame_queues[camera_id] = queue.Queue(maxsize=10)
                self.stop_flags[camera_id] = False
                self.latest_frames[camera_id] = (None, datetime.now())
                
        except Exception as e:
            logger.error(f"Error loading cameras from database: {str(e)}")
        finally:
            db.close()
    
    def add_camera(self, camera_id: str, source: str, zone_name: Optional[str] = None) -> bool:
        """
        Add a camera to be processed
        
        Args:
            camera_id: Unique identifier for the camera
            source: Video source (path, URL, or device ID)
            zone_name: Optional name for the camera zone
            
        Returns:
            Success status
        """
        if camera_id in self.cameras:
            logger.warning(f"Camera {camera_id} already exists. Please remove it first.")
            return False
        
        try:
            # Check if source is a numeric string (webcam device ID)
            if isinstance(source, str) and source.isdigit():
                source = int(source)
            
            # Create a capture object and verify it works
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                logger.error(f"Failed to open video source: {source}")
                return False
            
            # Store camera in database
            db = SessionLocal()
            try:
                from app.models.camera import Camera
                # Check if camera exists
                existing_camera = db.query(Camera).filter(Camera.name == camera_id).first()
                
                if existing_camera:
                    # Update existing camera - make sure we're setting all required fields
                    existing_camera.rtsp_url = str(source)
                    existing_camera.zones = {"default": zone_name or f"Zone {camera_id}"}
                    existing_camera.is_active = True
                    existing_camera.last_active = datetime.now()
                    logger.info(f"Updated existing camera record for {camera_id}")
                else:
                    # Create new camera
                    camera_db = Camera(
                        camera_id=camera_id,  # Explicitly set the camera_id field
                        name=camera_id,
                        rtsp_url=str(source),
                        zones={"default": zone_name or f"Zone {camera_id}"},
                        is_active=True,
                        last_active=datetime.now()
                    )
                    db.add(camera_db)
                    logger.info(f"Created new camera record for {camera_id}")
                
                # Make sure the commit succeeds
                db.commit()
                logger.info(f"Successfully committed camera {camera_id} to database")
            except Exception as e:
                logger.error(f"Database error while adding camera: {str(e)}")
                db.rollback()
                return False
            finally:
                db.close()
            
            # Store camera information
            self.cameras[camera_id] = {
                "source": source,
                "zone_name": zone_name or f"Zone {camera_id}",
                "status": "ready",
                "last_error": None,
                "started_at": None,
                "frames_processed": 0,
                "persons_detected": 0
            }
            
            # Initialize frame queue for this camera
            self.frame_queues[camera_id] = queue.Queue(maxsize=10)  # Limit queue size to avoid memory issues
            self.stop_flags[camera_id] = False
            self.latest_frames[camera_id] = (None, datetime.now())
            
            cap.release()
            logger.info(f"Camera {camera_id} added successfully with source {source}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding camera {camera_id}: {str(e)}")
            return False
    
    def start_camera(self, camera_id: str) -> bool:
        """
        Start processing a specific camera
        
        Args:
            camera_id: Camera identifier to start
            
        Returns:
            Success status
        """
        if camera_id not in self.cameras:
            logger.error(f"Camera {camera_id} not found")
            return False
        
        if camera_id in self.processing_threads and self.processing_threads[camera_id].is_alive():
            logger.warning(f"Camera {camera_id} is already running")
            return False
        
        self.stop_flags[camera_id] = False
        self.cameras[camera_id]["status"] = "starting"
        self.cameras[camera_id]["started_at"] = datetime.now()
        
        # Update database to mark camera as active and update last_active
        db = SessionLocal()
        try:
            from app.models.camera import Camera
            # Get camera from database
            camera_db = db.query(Camera).filter(Camera.name == camera_id).first()
            if camera_db:
                camera_db.is_active = True
                camera_db.last_active = datetime.now()
                db.commit()
                logger.info(f"Updated last_active timestamp for camera {camera_id}")
        except Exception as e:
            logger.error(f"Database error while updating camera status: {str(e)}")
        finally:
            db.close()
        
        # Create and start the processing thread
        process_thread = threading.Thread(
            target=self._process_camera_feed,
            args=(camera_id,),
            daemon=True
        )
        process_thread.start()
        
        self.processing_threads[camera_id] = process_thread
        logger.info(f"Started processing camera {camera_id}")
        return True
    
    def stop_camera(self, camera_id: str) -> bool:
        """
        Stop processing a camera
        
        Args:
            camera_id: Camera identifier to stop
            
        Returns:
            Success status
        """
        if camera_id not in self.processing_threads:
            logger.warning(f"Camera {camera_id} not found in processing threads")
            return False
            
        if not self.processing_threads[camera_id].is_alive():
            logger.warning(f"Camera {camera_id} is not running")
            return False
            
        # Set stop flag
        self.stop_flags[camera_id] = True
        
        # Wait for thread to finish
        self.processing_threads[camera_id].join(timeout=5.0)
        
        # Clean up
        if camera_id in self.processing_threads:
            del self.processing_threads[camera_id]
        if camera_id in self.stop_flags:
            del self.stop_flags[camera_id]
        if camera_id in self.frame_queues:
            del self.frame_queues[camera_id]
        if camera_id in self.latest_frames:
            del self.latest_frames[camera_id]
            
        logger.info(f"Stopped camera {camera_id}")
        return True
    
    def get_camera_status(self, camera_id: Optional[str] = None) -> Dict:
        """
        Get status of a specific camera or all cameras
        
        Args:
            camera_id: Optional camera identifier. If None, returns all cameras.
            
        Returns:
            Camera status information
        """
        if camera_id:
            if camera_id not in self.cameras:
                return {"error": f"Camera {camera_id} not found"}
            
            status = self.cameras[camera_id].copy()
            # Add runtime if the camera is active
            if status["started_at"]:
                runtime = datetime.now() - status["started_at"]
                status["runtime_seconds"] = runtime.total_seconds()
            
            return status
        else:
            # Return status of all cameras
            all_statuses = {}
            for cam_id, cam_info in self.cameras.items():
                status = cam_info.copy()
                if status["started_at"]:
                    runtime = datetime.now() - status["started_at"]
                    status["runtime_seconds"] = runtime.total_seconds()
                all_statuses[cam_id] = status
            
            return all_statuses
    
    def get_latest_frame(self, camera_id: str) -> Tuple[Optional[np.ndarray], datetime]:
        """
        Get the latest processed frame from a camera
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Tuple of (frame, timestamp)
        """
        if camera_id not in self.latest_frames:
            return None, datetime.now()
        
        return self.latest_frames[camera_id]
    
    def get_latest_frame_jpg(self, camera_id: str) -> Tuple[Optional[bytes], datetime]:
        """
        Get the latest processed frame as JPEG bytes
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Tuple of (jpeg_bytes, timestamp)
        """
        frame, timestamp = self.get_latest_frame(camera_id)
        
        if frame is None:
            return None, timestamp
        
        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes(), timestamp
    
    def start_all_cameras(self) -> Dict[str, bool]:
        """
        Start processing all registered cameras
        
        Returns:
            Dictionary of camera_id -> success status
        """
        results = {}
        for camera_id in self.cameras.keys():
            results[camera_id] = self.start_camera(camera_id)
        
        return results
    
    def stop_all_cameras(self) -> Dict[str, bool]:
        """
        Stop processing all cameras
        
        Returns:
            Dictionary of camera_id -> success status
        """
        results = {}
        for camera_id in list(self.cameras.keys()):
            results[camera_id] = self.stop_camera(camera_id)
        
        return results
    
    def _process_camera_feed(self, camera_id: str) -> None:
        """
        Process video feed from a camera (runs in a separate thread)
        
        Args:
            camera_id: Camera identifier to process
        """
        logger.info(f"Starting processing thread for camera {camera_id}")
        source = self.cameras[camera_id]["source"]
        
        # Configure target processing resolution
        target_width = 640   # Reduced resolution for processing
        target_height = 360  # Maintains 16:9 aspect ratio
        
        # Use the same approach as test-feed.py which successfully handles the stream
        try:
            # Use CAP_FFMPEG backend - critical for RTSP/HEVC streams
            logger.info(f"Opening stream with OpenCV CAP_FFMPEG: {source}")
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            
            # Set buffer size to match test-feed.py
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            
        except Exception as e:
            logger.error(f"Error opening video source for camera {camera_id}: {str(e)}")
            self.cameras[camera_id]["status"] = "error"
            self.cameras[camera_id]["last_error"] = f"Failed to open video source: {str(e)}"
            return
        
        if not cap.isOpened():
            logger.error(f"Failed to open video source for camera {camera_id}")
            self.cameras[camera_id]["status"] = "error"
            self.cameras[camera_id]["last_error"] = "Failed to open video source"
            return
            
        # Get the original resolution
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(f"Camera {camera_id} original resolution: {original_width}x{original_height}")
        
        # Store resolution in camera status
        self.cameras[camera_id].update({
            "original_width": original_width,
            "original_height": original_height,
            "target_width": target_width,
            "target_height": target_height
        })
        
        # Get frame rate
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30  # Default assumption
        
        # Adaptive frame skipping based on input resolution
        if original_width * original_height > 1920 * 1080:
            skip_factor = 10  # Higher skip for high-res streams
        else:
            skip_factor = 5
            
        logger.info(f"Camera {camera_id} using skip factor: {skip_factor} (processing every {skip_factor}th frame)")
        self.cameras[camera_id]["skip_factor"] = skip_factor
        
        # Frame processing parameters
        frame_interval = 0.01
        last_db_update = time.time()
        frame_count = 0
        db_update_interval = 60 # Update DB less frequently for general data
        
        self.cameras[camera_id]["status"] = "running"
        
        try:
            # Create a database session for this thread
            db = SessionLocal()
            
            while not self.stop_flags[camera_id]:
                start_time = time.time()
                
                # Read frame
                ret, frame = cap.read()
                
                if not ret:
                    # End of video or error - try to reconnect
                    logger.warning(f"Failed to read frame from camera {camera_id} - attempting reconnection")
                    
                    # Release current capture
                    cap.release()
                    
                    # Wait a bit before reconnecting
                    time.sleep(2)
                    
                    # Reopen with same approach as test-feed.py
                    try:
                        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
                        
                        if not cap.isOpened():
                            logger.error(f"Failed to reconnect to camera {camera_id}")
                            continue
                            
                    except Exception as reconnect_err:
                        logger.error(f"Error reconnecting to camera {camera_id}: {str(reconnect_err)}")
                        time.sleep(5)  # Wait longer before retrying
                        continue
                        
                    continue
                
                # Increment frame counter
                frame_count += 1
                timestamp = datetime.now()
                
                # Process every N frames for efficiency (using adaptive skip factor)
                if frame_count % skip_factor == 0:
                    # Explicitly resize frame for further processing
                    if frame.shape[1] != target_width or frame.shape[0] != target_height:
                        frame = cv2.resize(frame, (target_width, target_height))
                    
                    current_time_sec = time.time()
                    current_datetime = datetime.now()
                    hour_start_timestamp = current_datetime.replace(minute=0, second=0, microsecond=0)

                    # Run detection pipeline
                    detections = self.detector.detect_persons(frame)
                    
                    # Classify persons (staff vs customer)
                    detections = self.detector.classify_persons(frame, detections)
                    
                    # Track persons
                    tracked_persons = self.tracker.update(detections, frame)
                    logger.debug(f"Tracked {len(tracked_persons)} persons in frame {frame_count}")
                    
                    # Detect suspects
                    suspect_detections = self.suspect_tracking_service.detect_suspects(frame, camera_id)
                    
                    # Process suspect detections
                    for detection in suspect_detections:
                        # Save snapshot of the detection
                        snapshot_path = self._save_detection_snapshot(
                            frame, detection["location"], camera_id, frame_count
                        )
                        
                        # Track location
                        self.suspect_tracking_service.track_suspect_location(
                            detection["suspect_id"],
                            camera_id,
                            detection["location"],
                            detection["confidence"],
                            frame_count,
                            db
                        )
                        
                        # Generate alert
                        self.suspect_tracking_service.generate_alert(
                            detection["suspect_id"],
                            camera_id,
                            detection["confidence"],
                            snapshot_path,
                            db
                        )
                    
                    # Draw bounding boxes and tracking IDs
                    processed_frame = self._draw_detections(frame, tracked_persons, suspect_detections)
                    
                    # Add timestamp and camera ID
                    cv2.putText(
                        processed_frame,
                        f"{camera_id} | {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )
                    
                    # Update latest frame
                    self.latest_frames[camera_id] = (processed_frame, timestamp)
                    
                    # Update camera stats
                    self.cameras[camera_id]["frames_processed"] += 1
                    self.cameras[camera_id]["persons_detected"] = len(tracked_persons)
                    
                    # --- Footfall and Demographics Aggregation --- 
                    try:
                        unique_persons_this_frame = set()
                        persons_with_demographics = 0
                        for person in tracked_persons:
                            # Ensure person is a dictionary and get track_id safely
                            if not isinstance(person, dict):
                                logger.warning("Skipping non-dict item in tracked_persons")
                                continue
                                
                            track_id = person.get('track_id') 
                            
                            # Check 1: Skip if track_id is missing
                            if track_id is None:
                                logger.debug("Skipping person with missing track_id")
                                continue
                                
                            # Check 2: Skip if already processed this unique ID in this frame
                            if track_id in unique_persons_this_frame:
                                logger.debug(f"Skipping already counted track_id {track_id} in this frame")
                                continue
                            
                            # --- If we reach here, track_id is valid and unique for this frame --- 
                            logger.debug(f"Processing track_id {track_id}")
                            unique_persons_this_frame.add(track_id)
                            self.hourly_footfall_tracker[camera_id][hour_start_timestamp].add(track_id)

                            # Estimate demographics (requires bbox)
                            if self.demographics_estimator and 'bbox' in person:
                                try:
                                    x1, y1, x2, y2 = person['bbox']
                                    # Ensure coordinates are valid integers
                                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                                    # Ensure coordinates are within frame bounds and width/height > 0
                                    h, w = frame.shape[:2]
                                    x1, y1 = max(0, x1), max(0, y1)
                                    x2, y2 = min(w, x2), min(h, y2)
                                    if x1 < x2 and y1 < y2:
                                        person_crop = frame[y1:y2, x1:x2] 
                                        if person_crop.size > 0:
                                            demographics = self.demographics_estimator(person_crop)
                                            if demographics and demographics.get('gender') and demographics.get('age_group'):
                                                category = f"{demographics['gender']}_{demographics['age_group']}"
                                                self.hourly_demographics_tracker[camera_id][hour_start_timestamp][category] += 1
                                                person['demographics'] = demographics 
                                                persons_with_demographics += 1
                                    else:
                                        logger.debug(f"Skipping demo for track_id {track_id}: Invalid bbox after clamping [{x1},{y1},{x2},{y2}] for frame {w}x{h}")
                                except Exception as demo_err:
                                     logger.error(f"Error during individual demographic estimation for track_id {track_id}: {demo_err}")
                                     
                        # Log aggregation counts for this frame
                        logger.debug(f"Aggregated Frame: Footfall unique IDs: {len(unique_persons_this_frame)}, Demo estimates: {persons_with_demographics}")
                    except Exception as agg_err:
                        logger.error(f"Error during outer footfall/demographics aggregation loop: {agg_err}")
                    # --- End Aggregation --- 
                
                    # Periodically store aggregated data
                    current_time_sec = time.time() # Ensure this is recalculated here
                    if current_time_sec - self.last_aggregation_time >= self.aggregation_interval:
                        logger.info(f"Aggregation interval reached. Calling _store_aggregated_data. Time since last: {current_time_sec - self.last_aggregation_time:.1f}s")
                        self._store_aggregated_data(db)
                        self.last_aggregation_time = current_time_sec # Reset time AFTER calling store
                
                # Simple frame rate control
                processing_time = time.time() - start_time
                sleep_time = max(0.001, frame_interval - processing_time)
                time.sleep(sleep_time)
        
        except Exception as e:
            logger.error(f"Error processing camera {camera_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.cameras[camera_id]["status"] = "error"
            self.cameras[camera_id]["last_error"] = str(e)
        
        finally:
            # Clean up
            cap.release()
            db.close()
            self.cameras[camera_id]["status"] = "stopped"
            logger.info(f"Stopped processing thread for camera {camera_id}")
    
    def _draw_detections(self, frame: np.ndarray, detections: List[Dict], suspect_detections: List[Dict] = None) -> np.ndarray:
        """
        Draw detection boxes and information on frame
        
        Args:
            frame: Input frame
            detections: List of detection dictionaries
            suspect_detections: List of suspect detection dictionaries
            
        Returns:
            Frame with detections drawn on it
        """
        result_frame = frame.copy()
        
        # Draw regular detections
        for det in detections:
            if "bbox" not in det:
                continue
                
            x1, y1, x2, y2 = det["bbox"]
            track_id = det.get("track_id", "?")
            confidence = det.get("confidence", 0)
            is_staff = det.get("is_staff", False)
            
            # Choose color based on staff status
            color = (0, 255, 0) if is_staff else (0, 0, 255)
            
            # Draw bounding box
            cv2.rectangle(result_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"ID:{track_id} {'Staff' if is_staff else 'Customer'} {confidence:.2f}"
            cv2.putText(
                result_frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )
        
        # Draw suspect detections
        if suspect_detections:
            for det in suspect_detections:
                loc = det["location"]
                confidence = det["confidence"]
                
                # Draw red bounding box for suspects
                cv2.rectangle(
                    result_frame,
                    (loc["left"], loc["top"]),
                    (loc["right"], loc["bottom"]),
                    (0, 0, 255),
                    3
                )
                
                # Draw suspect label
                label = f"SUSPECT {confidence:.2f}"
                cv2.putText(
                    result_frame,
                    label,
                    (loc["left"], loc["top"] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )
        
        # Add total count
        cv2.putText(
            result_frame,
            f"People: {len(detections)}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        return result_frame
    
    def _store_detection_data(self, db: Session, camera_id: str, 
                             tracked_persons: List[Dict], timestamp: datetime) -> None:
        """
        Store detection data in the database
        
        Args:
            db: Database session
            camera_id: Camera identifier
            tracked_persons: List of tracked person dictionaries
            timestamp: Timestamp for the detections
        """
        # Create detection event
        detection_event = DetectionEvent(
            timestamp=timestamp,
            camera_id=camera_id,
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
                        "confidence": p.get("confidence", 0)
                    } for p in tracked_persons
                ]
            }
        )
        
        db.add(detection_event)
    
    def _store_analytics_data(self, db: Session, camera_id: str, 
                             analytics: Dict, timestamp: datetime) -> None:
        """
        Store analytics data in the database
        
        Args:
            db: Database session
            camera_id: Camera identifier
            analytics: Analytics dictionary
            timestamp: Timestamp for the analytics
        """
        # Get camera by name
        from app.models.camera import Camera
        camera = db.query(Camera).filter(Camera.name == camera_id).first()
        if not camera:
            logger.error(f"Camera {camera_id} not found in database")
            return

        # Create analytics entry
        analytics_entry = Analytics(
            timestamp=timestamp,
            camera_id=camera.camera_id,
            total_people=analytics.get("person_count", 0),
            people_per_zone=analytics.get("zone_counts", {}),
            movement_patterns=analytics.get("movement_patterns", {}),
            dwell_times=analytics.get("dwell_times", {}),
            entry_count=analytics.get("entries", 0),
            exit_count=analytics.get("exits", 0)
        )
        
        db.add(analytics_entry)
    
    def _store_alert_data(self, db: Session, camera_id: str, 
                         alert: Dict, timestamp: datetime) -> None:
        """
        Store alert data in the database
        
        Args:
            db: Database session
            camera_id: Camera identifier
            alert: Alert dictionary
            timestamp: Timestamp for the alert
        """
        # Create alert entry
        alert_entry = Alert(
            timestamp=timestamp,
            alert_type=alert["alert_type"],
            severity=alert["severity"],
            track_id=alert["track_id"],
            description=f"{camera_id}: {alert['description']}",
            snapshot_path=alert.get("snapshot_path")
        )
        
        db.add(alert_entry)
    
    def _save_frame(self, camera_id: str, frame: np.ndarray, timestamp: datetime) -> str:
        """
        Save a frame to disk
        
        Args:
            camera_id: Camera identifier
            frame: Frame to save
            timestamp: Timestamp for the frame
            
        Returns:
            Path where the frame was saved
        """
        # Create directory structure
        date_str = timestamp.strftime("%Y-%m-%d")
        camera_dir = os.path.join(self.frames_dir, camera_id, date_str)
        os.makedirs(camera_dir, exist_ok=True)
        
        # Create filename with timestamp
        filename = f"{timestamp.strftime('%H-%M-%S')}.jpg"
        filepath = os.path.join(camera_dir, filename)
        
        # Save frame
        cv2.imwrite(filepath, frame)
        
        return filepath
    
    def _save_detection_snapshot(self, frame: np.ndarray, location: Dict, 
                               camera_id: str, frame_number: int) -> str:
        """
        Save a snapshot of a detection
        
        Args:
            frame: Input frame
            location: Detection location dictionary
            camera_id: Camera identifier
            frame_number: Current frame number
            
        Returns:
            Path to saved snapshot
        """
        try:
            # Create directory structure
            date_str = datetime.now().strftime("%Y-%m-%d")
            snapshots_dir = os.path.join("data", "snapshots", camera_id, date_str)
            os.makedirs(snapshots_dir, exist_ok=True)
            
            # Save full frame with detection box
            full_frame = frame.copy()
            cv2.rectangle(
                full_frame,
                (location["left"], location["top"]),
                (location["right"], location["bottom"]),
                (0, 0, 255),  # Red box for suspect
                3
            )
            
            # Add text label
            cv2.putText(
                full_frame,
                "SUSPECT DETECTED",
                (location["left"], location["top"] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )
            
            # Save full frame
            timestamp = int(time.time())
            filename = f"detection_{frame_number}_{timestamp}.jpg"
            filepath = os.path.join(snapshots_dir, filename)
            cv2.imwrite(filepath, full_frame)
            
            # Also save the cropped ROI as a thumbnail
            roi = frame[location["top"]:location["bottom"], 
                       location["left"]:location["right"]]
            thumb_filename = f"detection_{frame_number}_{timestamp}_thumb.jpg"
            thumb_filepath = os.path.join(snapshots_dir, thumb_filename)
            cv2.imwrite(thumb_filepath, roi)
            
            return filepath
        except Exception as e:
            logger.error(f"Error saving detection snapshot: {str(e)}")
            return ""
    
    def _auto_restart_active_cameras(self):
        """
        Automatically restart cameras that were recently active
        This helps maintain camera operation across server restarts
        """
        recent_active_threshold = datetime.now() - timedelta(hours=1)
        db = SessionLocal()
        try:
            from app.models.camera import Camera
            # Get cameras that were active in the last hour
            recent_cameras = db.query(Camera).filter(
                Camera.is_active == True,
                Camera.last_active >= recent_active_threshold
            ).all()
            
            if recent_cameras:
                logger.info(f"Auto-starting {len(recent_cameras)} recently active cameras")
                
                # Start cameras in a separate thread to not block server startup
                restart_thread = threading.Thread(
                    target=self._delayed_camera_restart,
                    args=([cam.name for cam in recent_cameras],),
                    daemon=True
                )
                restart_thread.start()
        except Exception as e:
            logger.error(f"Error auto-restarting cameras: {str(e)}")
        finally:
            db.close()
    
    def _delayed_camera_restart(self, camera_ids: List[str]):
        """
        Start cameras after a short delay to allow the server to fully initialize
        
        Args:
            camera_ids: List of camera IDs to start
        """
        # Wait a few seconds to ensure server is fully up
        time.sleep(5)
        
        for camera_id in camera_ids:
            try:
                if camera_id in self.cameras:
                    logger.info(f"Auto-restarting camera {camera_id}")
                    self.start_camera(camera_id)
                    # Add a small delay between starts to avoid overload
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Error auto-restarting camera {camera_id}: {str(e)}")

    def _initialize_demographics_estimator(self):
        if not deepface_available:
            logger.error("Cannot initialize DeepFace estimator: Library not available.")
            return None
            
        logger.info("Initializing DeepFace demographics estimator.")
        # Pre-load models (optional but recommended for performance)
        # Removed incorrect pre-loading calls:
        # try:
        #     DeepFace.build_model('Age') # <-- Incorrect usage
        #     DeepFace.build_model('Gender') # <-- Incorrect usage
        #     logger.info("DeepFace Age and Gender models pre-loaded.")
        # except Exception as e:
        #     logger.warning(f"Could not pre-load DeepFace models: {e}")

        def estimate_demographics_deepface(image_crop: np.ndarray):
            if image_crop.size == 0:
                return None
            try:
                # Analyze face for age and gender
                # enforce_detection=False prevents errors if no face is clearly found
                # Use a specific detector backend if default causes issues (e.g., 'opencv', 'ssd')
                result = DeepFace.analyze(
                    img_path=image_crop, 
                    actions=['age', 'gender'],
                    enforce_detection=False,
                    detector_backend='retinaface' # Try retinaface or opencv
                )
                
                # DeepFace returns a list, usually with one element if face is found
                if isinstance(result, list) and len(result) > 0:
                    analysis = result[0]
                    age = analysis.get('age')
                    gender = analysis.get('dominant_gender')

                    if age is not None and gender is not None:
                        # Map age to categories
                        if age < 18:
                            age_group = "child"
                        elif age < 35:
                            age_group = "young_adult"
                        elif age < 60:
                            age_group = "adult"
                        else:
                            age_group = "senior"
                            
                        # Map gender to lowercase
                        gender_mapped = "male" if gender == "Man" else "female"
                        
                        logger.debug(f"Demographics estimated: Age={age}, Gender={gender}, Group={age_group}")
                        return {"gender": gender_mapped, "age_group": age_group}
            except ValueError as ve:
                # Handle cases where DeepFace doesn't find a face clearly
                logger.debug(f"DeepFace could not find a face or analyze: {ve}")
            except Exception as e:
                logger.error(f"Error during DeepFace analysis: {e}")
            return None # Return None if analysis fails or no face is found
            
        return estimate_demographics_deepface

    def _store_aggregated_data(self, db: Session):
        """Store aggregated hourly footfall and demographics data in the database."""
        # Use a copy to avoid modifying dict while iterating (though clearing later helps)
        current_footfall = self.hourly_footfall_tracker.copy()
        current_demographics = self.hourly_demographics_tracker.copy()

        # Optional: Clear trackers immediately if confident in copy/processing
        # self.hourly_footfall_tracker.clear()
        # self.hourly_demographics_tracker.clear()

        logger.info(f"Storing aggregated hourly data. Footfall hours: {len(current_footfall)}, Demo hours: {len(current_demographics)}")
        if not current_footfall and not current_demographics:
            return # Nothing to store

        try:
            # Store Footfall
            for cam_id, hour_data in current_footfall.items():
                for hour_ts, track_ids in hour_data.items():
                    count = len(track_ids)
                    if count == 0: continue # Skip if no count for this hour yet
                    
                    # Upsert logic using merge for potential concurrent updates
                    stmt = insert(HourlyFootfall).values(
                        camera_id=cam_id, 
                        timestamp_hour=hour_ts, 
                        unique_person_count=count
                    ).on_conflict_do_update(
                        index_elements=['camera_id', 'timestamp_hour'],
                        set_=dict(unique_person_count=count) # Overwrite with latest count for the hour
                    )
                    db.execute(stmt)
                    logger.debug(f"Upserting footfall: {cam_id} @ {hour_ts} -> {count}")
            
            # Store Demographics
            for cam_id, hour_data in current_demographics.items():
                for hour_ts, demo_counts in hour_data.items():
                    if not demo_counts: continue # Skip empty entries
                    
                    # Fetch existing first to merge JSONB correctly
                    existing = db.query(HourlyDemographics).filter_by(camera_id=cam_id, timestamp_hour=hour_ts).with_for_update().first()
                    
                    if existing:
                        # Merge counts properly - Essential for JSONB
                        merged_data = existing.demographics_data.copy() if existing.demographics_data else {}
                        for category, count in demo_counts.items():
                            merged_data[category] = merged_data.get(category, 0) + count
                        
                        # Only update if data actually changed
                        if existing.demographics_data != merged_data:
                            existing.demographics_data = merged_data 
                            logger.debug(f"Updating demographics JSONB: {cam_id} @ {hour_ts}")
                        else:
                             logger.debug(f"Demographics data unchanged, skipping update: {cam_id} @ {hour_ts}")
                    else:
                        record = HourlyDemographics(camera_id=cam_id, timestamp_hour=hour_ts, demographics_data=demo_counts)
                        db.add(record)
                        logger.debug(f"Inserting demographics: {cam_id} @ {hour_ts}")

            db.commit()
            logger.info("Aggregated data committed successfully.")

            # Clear trackers AFTER successful commit
            self.hourly_footfall_tracker.clear()
            self.hourly_demographics_tracker.clear()

        except Exception as e:
            logger.error(f"Error storing aggregated data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            db.rollback()

# Singleton instance
live_camera_processor = LiveCameraProcessor()