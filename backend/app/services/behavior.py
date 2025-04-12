# app/services/behavior.py (simplified version without zones)
import numpy as np
import cv2
import mediapipe as mp
from typing import Dict, List, Any, Tuple
import time
import logging
import json
import uuid
from datetime import datetime, timedelta
import os
import io

from app.core.config import settings
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)

class BehaviorAnalysisService:
    """Service for analyzing person behavior for security surveillance"""
    
    def __init__(self):
        """Initialize behavior analysis service"""
        # Initialize MediaPipe Pose for pose detection
        self.mp_pose = mp.solutions.pose
                
        # Configure MediaPipe with standard options
        try:
            self.pose = self.mp_pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                model_complexity=1,  # Medium complexity for balance of speed and accuracy
                enable_segmentation=False  # Turn off segmentation to improve performance
            )
            logger.info("MediaPipe Pose initialized with standard configuration")
        except Exception as e:
            logger.warning(f"Failed to initialize MediaPipe Pose: {e}. Using default configuration.")
            # Fallback to default if custom configuration fails
            self.pose = self.mp_pose.Pose()
        
        # Track person data
        self.last_seen = {}  # track_id -> timestamp
        self.suspicious_activity = {}  # track_id -> suspicious_activity_count
        self.last_pose_alert_time = {} # track_id -> timestamp of last pose alert
        self.pose_alert_cooldown = 10 # Cooldown in seconds (changed to 10 seconds)
        
        # Track loitering data
        self.first_seen_position = {}  # track_id -> (x, y, timestamp)
        self.loitering_alerts_sent = set()  # Set of track_ids for which loitering alerts were already sent
        self.loitering_threshold = 300  # Changed to 300 seconds (5 minutes)
        
        logger.info("Behavior analysis service initialized")
        
        self.s3_service = S3Service()
    
    def analyze_frame(self, frame: np.ndarray, tracked_persons: List[Dict[str, Any]], 
                     timestamp: float) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Analyze behavior in the current frame
        
        Args:
            frame: Current video frame
            tracked_persons: List of tracked person dictionaries
            timestamp: Frame timestamp
            
        Returns:
            Tuple of (analytics_data, alerts)
        """
        analytics_data = []
        alerts = []
        
        # Skip processing if no frame or no tracked persons
        if frame is None or not isinstance(tracked_persons, list):
            logger.warning("Invalid frame or tracked_persons data")
            return [], []
        
        try:
            # Resize frame to 720p height for processing efficiency
            h, w = frame.shape[:2]
            target_height = 720
            scale_factor = target_height / h
            target_width = int(w * scale_factor)
            resized_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
            logger.debug(f"Resized frame from {w}x{h} to {target_width}x{target_height}")

            for person in tracked_persons:
                # Skip if person doesn't have required fields
                if not isinstance(person, dict) or 'track_id' not in person or 'bbox' not in person:
                    continue
                    
                track_id = person.get('track_id')
                if track_id is None:
                    continue
                    
                # Initialize tracking data for new persons
                if track_id not in self.last_seen:
                    self.last_seen[track_id] = timestamp
                    self.suspicious_activity[track_id] = 0
                    
                    # Initialize loitering detection
                    if 'bbox' in person:
                        try:
                            x1, y1, x2, y2 = person['bbox']
                            center_x = (x1 + x2) / 2
                            center_y = (y1 + y2) / 2
                            self.first_seen_position[track_id] = (center_x, center_y, timestamp)
                        except (ValueError, TypeError):
                            logger.error(f"Invalid bbox format for track_id {track_id}")
                
                # Check for suspicious poses using the RESIZED frame and SCALED bbox
                try:
                    bbox = person['bbox']
                    x1, y1, x2, y2 = bbox
                    
                    # Scale the bounding box coordinates
                    scaled_bbox = (
                        int(x1 * scale_factor),
                        int(y1 * scale_factor),
                        int(x2 * scale_factor),
                        int(y2 * scale_factor)
                    )
                    
                    pose_result = self._analyze_pose(resized_frame, scaled_bbox)
                    
                    if pose_result['suspicious']:
                        self.suspicious_activity[track_id] += 1
                        
                        # Generate alert if suspicious activity threshold reached
                        # Use pose severity to determine alert threshold (higher severity needs fewer frames)
                        severity = pose_result.get('severity', 3)
                        threshold = 5 if severity == 1 else (3 if severity == 2 else 1)
                        
                        # Check cooldown before sending alert
                        last_alert_time = self.last_pose_alert_time.get(track_id, 0)
                        cooldown_passed = (timestamp - last_alert_time) > self.pose_alert_cooldown

                        if self.suspicious_activity[track_id] >= threshold and cooldown_passed:
                            alert = {
                                'timestamp': datetime.now().isoformat(),
                                'alert_type': 'suspicious_pose',
                                'severity': severity,
                                'track_id': track_id,
                                'description': f"Suspicious posture detected: {pose_result['details']}",
                                'bbox': bbox, # Use ORIGINAL bbox for the alert data
                                'is_staff': person.get('is_staff', False)
                            }
                            
                            # Capture frame snapshot using ORIGINAL frame and bbox
                            snapshot_path = self.capture_frame_on_alert(frame, alert)
                            if snapshot_path:
                                alert['snapshot_path'] = snapshot_path
                                
                            alerts.append(alert)
                            # Reset counter and update last alert time after alert
                            self.suspicious_activity[track_id] = 0
                            self.last_pose_alert_time[track_id] = timestamp
                except Exception as e:
                    logger.error(f"Error in pose analysis for track_id {track_id}: {str(e)}")
                
                # Check for loitering behavior
                try:
                    if self._detect_loitering(person, timestamp, track_id):
                        # Only send alert if we haven't sent one for this person already
                        if track_id not in self.loitering_alerts_sent:
                            alert = {
                                'timestamp': datetime.now().isoformat(),
                                'alert_type': 'loitering',
                                'severity': 2,  # Medium severity
                                'track_id': track_id,
                                'description': f"Person loitering for over 5 minutes",
                                'bbox': bbox, # Use ORIGINAL bbox for alert data
                                'is_staff': person.get('is_staff', False)
                            }
                            
                            # Capture frame snapshot using ORIGINAL frame and bbox
                            snapshot_path = self.capture_frame_on_alert(frame, alert)
                            if snapshot_path:
                                alert['snapshot_path'] = snapshot_path
                            
                            alerts.append(alert)
                            self.loitering_alerts_sent.add(track_id)
                            logger.info(f"Loitering alert generated for track_id {track_id}")
                except Exception as e:
                    logger.error(f"Error in loitering detection for track_id {track_id}: {str(e)}")
                
                # Update last seen timestamp
                self.last_seen[track_id] = timestamp
            
            # Generate basic analytics
            try:
                analytics = {
                    'timestamp': datetime.now().isoformat(),
                    'person_count': len(tracked_persons),
                    'staff_count': sum(1 for p in tracked_persons if p.get('is_staff', False)),
                    'customer_count': sum(1 for p in tracked_persons if not p.get('is_staff', False)),
                    'suspicious_activity_count': sum(1 for p in tracked_persons 
                                              if self.suspicious_activity.get(p.get('track_id', ''), 0) > 0),
                    'loitering_count': len(self.loitering_alerts_sent)
                }
                analytics_data.append(analytics)
            except Exception as e:
                logger.error(f"Error generating analytics data: {str(e)}")
            
            # Clean up tracking data for persons not seen recently
            self._cleanup_tracking_data(timestamp)
            
        except Exception as e:
            logger.error(f"Error in behavior analysis: {str(e)}")
        
        return analytics_data, alerts
    
    def _detect_loitering(self, person: Dict[str, Any], current_time: float, track_id: str) -> bool:
        """
        Detect if a person is loitering in an area
        
        Args:
            person: Dictionary containing person data
            current_time: Current timestamp
            track_id: Person's tracking ID
            
        Returns:
            True if loitering is detected, False otherwise
        """
        # Skip if we don't have initial position data
        if track_id not in self.first_seen_position:
            return False
            
        # Get current position
        if 'bbox' not in person:
            return False
            
        x1, y1, x2, y2 = person['bbox']
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Get initial position and time
        initial_x, initial_y, initial_time = self.first_seen_position[track_id]
        
        # Calculate time spent
        time_spent = current_time - initial_time
        
        # Calculate movement distance
        movement_distance = np.sqrt((center_x - initial_x)**2 + (center_y - initial_y)**2)
        
        # Loitering is when a person stays in roughly the same area for too long
        # We use a movement threshold of 100 pixels to determine if they've moved significantly
        if time_spent > self.loitering_threshold and movement_distance < 100:
            return True
            
        # If person moved significantly, update their first seen position
        if movement_distance > 100:
            self.first_seen_position[track_id] = (center_x, center_y, current_time)
            
        return False
    
    def capture_frame_on_alert(self, frame: np.ndarray, alert: dict) -> str:
        """
        Capture a frame when an alert is triggered and save it to S3
        
        Args:
            frame: The current video frame
            alert: The alert data dictionary
            
        Returns:
            S3 URL of the saved snapshot or None if failed
        """
        try:
            # Generate a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_type = alert['alert_type']
            alert_id = alert.get('id', uuid.uuid4().hex[:8])
            filename = f"alert_{alert_type}_{alert_id}_{timestamp}.jpg"
            
            # Create a directory structure based on date for S3 key
            date_dir = datetime.now().strftime("%Y/%m/%d")
            s3_key = f"{date_dir}/{filename}"
            
            # Extract relevant portion of frame if bounding box is available
            if 'bbox' in alert:
                x1, y1, x2, y2 = alert['bbox']
                # Add some padding around the bounding box
                height, width = frame.shape[:2]
                padding = 50
                x1 = max(0, x1 - padding)
                y1 = max(0, y1 - padding)
                x2 = min(width, x2 + padding)
                y2 = min(height, y2 + padding)
                frame_to_save = frame[y1:y2, x1:x2]
            else:
                frame_to_save = frame
            
            # Convert frame to bytes
            is_success, buffer = cv2.imencode(".jpg", frame_to_save)
            if not is_success:
                raise Exception("Failed to encode image")
            
            # Create file-like object from buffer
            file_obj = io.BytesIO(buffer.tobytes())
            
            # Upload to S3
            s3_url = self.s3_service.upload_file(
                file_obj=file_obj,
                file_name=s3_key,
                content_type='image/jpeg'
            )
            
            if s3_url:
                return s3_url
            else:
                raise Exception("Failed to upload to S3")
            
        except Exception as e:
            logger.error(f"Error capturing frame snapshot: {str(e)}")
            return None
    
    def _cleanup_tracking_data(self, current_timestamp: float) -> None:
        """
        Remove tracking data for persons not seen recently
        
        Args:
            current_timestamp: Current frame timestamp
        """
        stale_tracks = []
        
        for track_id, last_seen_time in self.last_seen.items():
            if current_timestamp - last_seen_time > 60:  # 1 minute timeout
                stale_tracks.append(track_id)
        
        for track_id in stale_tracks:
            if track_id in self.last_seen:
                del self.last_seen[track_id]
            if track_id in self.suspicious_activity:
                del self.suspicious_activity[track_id]
            if track_id in self.first_seen_position:
                del self.first_seen_position[track_id]
            if track_id in self.loitering_alerts_sent:
                self.loitering_alerts_sent.remove(track_id)
    
    def _analyze_pose(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """
        Analyze person pose for suspicious behavior related to theft
        
        Args:
            frame: Current video frame
            bbox: Person bounding box
            
        Returns:
            Dictionary with pose analysis results
        """
        x1, y1, x2, y2 = bbox
        
        # Extract person ROI
        person_roi = frame[y1:y2, x1:x2]
        if person_roi.size == 0:
            return {'suspicious': False, 'details': 'Invalid ROI'}
        
        # Convert to RGB for MediaPipe
        rgb_roi = cv2.cvtColor(person_roi, cv2.COLOR_BGR2RGB)
        
        # Process with a try-except block to handle potential errors
        try:
            # Modify MediaPipe options to handle timestamp errors
            # Get pose landmarks
            results = self.pose.process(rgb_roi)
            
            if not results.pose_landmarks:
                return {'suspicious': False, 'details': 'No pose detected'}
            
            landmarks = results.pose_landmarks.landmark
            h, w, _ = person_roi.shape
            
            # Get key body points
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
            right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            
            # Enhanced theft posture detection
            
            # 1. Hand near shelf/display - check if hands are extended
            hands_extended = (left_wrist.x < 0.2 or left_wrist.x > 0.8 or 
                              right_wrist.x < 0.2 or right_wrist.x > 0.8)
            
            # 2. Check for hands near pockets or waistband
            left_hand_near_pocket = self._calculate_distance(left_wrist, left_hip) < 0.15
            right_hand_near_pocket = self._calculate_distance(right_wrist, right_hip) < 0.15
            hands_near_pockets = left_hand_near_pocket or right_hand_near_pocket
            
            # 3. Check for concealment posture - arms crossing body
            left_arm_crossing = (left_wrist.x > nose.x) if (left_shoulder.x < nose.x) else (left_wrist.x < nose.x)
            right_arm_crossing = (right_wrist.x < nose.x) if (right_shoulder.x > nose.x) else (right_wrist.x > nose.x)
            concealment_posture = left_arm_crossing or right_arm_crossing
            
            # 4. Check for bent posture (potential picking up)
            bent_over = (nose.y > (left_hip.y + right_hip.y) / 2 - 0.1)
            
            # 5. Specific grabbing motion - elbows bent with hands extended
            left_grabbing = (left_elbow.y < left_shoulder.y) and (left_wrist.y < left_elbow.y)
            right_grabbing = (right_elbow.y < right_shoulder.y) and (right_wrist.y < right_elbow.y)
            grabbing_motion = left_grabbing or right_grabbing
            
            # Determine suspiciousness based on combined postures
            # High suspicion - multiple suspicious postures
            if (hands_near_pockets and (concealment_posture or bent_over)):
                return {
                    'suspicious': True,
                    'details': 'Potential theft: hands near pockets with concealment or bending',
                    'severity': 3  # High severity
                }
            elif (hands_extended and bent_over):
                return {
                    'suspicious': True,
                    'details': 'Potential theft: reaching for items while bent over',
                    'severity': 3  # High severity
                }
            elif (grabbing_motion and concealment_posture):
                return {
                    'suspicious': True,
                    'details': 'Potential theft: grabbing motion with concealment posture',
                    'severity': 3  # High severity
                }
            # Medium suspicion - single suspicious posture
            elif hands_near_pockets:
                return {
                    'suspicious': True,
                    'details': 'Suspicious: hands near pockets or waistband',
                    'severity': 2  # Medium severity
                }
            elif concealment_posture:
                return {
                    'suspicious': True,
                    'details': 'Suspicious: possible concealment posture',
                    'severity': 2  # Medium severity
                }
            elif grabbing_motion:
                return {
                    'suspicious': True,
                    'details': 'Suspicious: grabbing motion detected',
                    'severity': 2  # Medium severity
                }
            
            return {'suspicious': False, 'details': 'Normal posture', 'severity': 1}
            
        except Exception as e:
            logger.error(f"Error in pose analysis: {str(e)}")
            return {'suspicious': False, 'details': f'Error in pose analysis: {str(e)}', 'severity': 1}
    
    def _calculate_distance(self, landmark1, landmark2) -> float:
        """Calculate Euclidean distance between two landmarks"""
        return np.sqrt((landmark1.x - landmark2.x)**2 + (landmark1.y - landmark2.y)**2)