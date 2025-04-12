import cv2
from typing import Dict, Any
import threading
import time
from datetime import datetime

from app.services.computer_vision import ComputerVisionAnalyzer
from app.core.database import SessionLocal
from app.models.analytics import Analytics

class CameraService:
    def __init__(self, camera_id: int, rtsp_url: str, zones: Dict[str, list]):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.zones = zones
        self.analyzer = ComputerVisionAnalyzer()
        self.is_running = False
        self.thread = None
        
    def start(self):
        """Start the camera analysis thread"""
        if self.is_running:
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._process_stream)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """Stop the camera analysis thread"""
        self.is_running = False
        if self.thread:
            self.thread.join()
            
    def _process_stream(self):
        """Process the camera stream and perform analysis"""
        # Open video capture with improved settings for high-res streams
        cap = cv2.VideoCapture(self.rtsp_url)
        
        # Increase buffer size for HEVC streams
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 5)
        
        # Try to enable hardware acceleration if available
        cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
        
        if not cap.isOpened():
            print(f"Error: Could not open camera {self.camera_id}")
            return
            
        # Get the original resolution
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Configure target processing resolution
        target_width = 640
        target_height = 360
        
        # Determine if we need to downsample frames
        downsampling_needed = original_width > 1280 or original_height > 720
        
        # Calculate adaptive analysis interval based on resolution
        # For higher resolutions, we'll analyze less frequently
        if original_width * original_height > 1920 * 1080:
            analysis_interval = max(5, min(10, int((original_width * original_height) / (640 * 360) / 2)))
        else:
            analysis_interval = 5  # Default interval for standard resolutions
            
        print(f"Camera {self.camera_id} resolution: {original_width}x{original_height}, analysis interval: {analysis_interval}s")
            
        last_analysis_time = time.time()
        frames_processed = 0
        
        try:
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    print(f"Error: Could not read frame from camera {self.camera_id}")
                    # Try to reconnect
                    time.sleep(2)
                    cap.release()
                    cap = cv2.VideoCapture(self.rtsp_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 5)
                    continue
                    
                current_time = time.time()
                
                # Analyze frame at the specified interval
                if current_time - last_analysis_time >= analysis_interval:
                    # Downsample frame if needed before processing
                    if downsampling_needed:
                        analysis_frame = cv2.resize(frame, (target_width, target_height))
                    else:
                        analysis_frame = frame.copy()
                    
                    # Process frame and get analysis results
                    start_process = time.time()
                    results = self.analyzer.process_frame(analysis_frame, self.zones)
                    process_time = time.time() - start_process
                    
                    # Save results to database
                    self._save_analysis(results)
                    
                    # Update counters and timing
                    frames_processed += 1
                    last_analysis_time = current_time
                    
                    print(f"Camera {self.camera_id}: Frame processed in {process_time:.3f}s, detected {results['total_people']} people")
                
                # Sleep briefly to prevent CPU overload
                time.sleep(0.01)
                    
        finally:
            cap.release()
            
    def _save_analysis(self, results: Dict[str, Any]):
        """Save analysis results to the database"""
        db = SessionLocal()
        try:
            analytics = Analytics(
                camera_id=self.camera_id,
                timestamp=datetime.utcnow(),
                total_people=results["total_people"],
                people_per_zone=results["people_per_zone"],
                movement_patterns=results["movement_patterns"],
                dwell_times=results["dwell_times"]
            )
            
            db.add(analytics)
            db.commit()
        except Exception as e:
            print(f"Error saving analytics: {str(e)}")
            db.rollback()
        finally:
            db.close()