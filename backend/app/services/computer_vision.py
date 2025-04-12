import cv2
import numpy as np
from ultralytics import YOLO
from typing import Dict, Any, List, Tuple
import time
from collections import defaultdict

class ComputerVisionAnalyzer:
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model = YOLO(model_path)
        self.track_history = defaultdict(lambda: [])
        self.zone_occupancy = defaultdict(int)
        self.dwell_times = defaultdict(lambda: defaultdict(float))
        self.last_seen = defaultdict(float)
        
    def process_frame(self, frame: np.ndarray, zones: Dict[str, List[Tuple[int, int]]]) -> Dict[str, Any]:
        """
        Process a single frame using YOLO for object detection and tracking.
        
        Args:
            frame: Input frame from camera
            zones: Dictionary of zone names and their polygon coordinates
            
        Returns:
            Dictionary containing analysis results
        """
        # Run YOLO detection
        results = self.model.track(frame, persist=True, classes=[0])  # class 0 is 'person'
        
        # Initialize frame results
        frame_results = {
            "total_people": 0,
            "people_per_zone": {},
            "dwell_times": {},
            "movement_patterns": {}
        }
        
        if results[0].boxes.id is None:
            return frame_results
            
        # Get tracked objects
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.int().cpu().tolist()
        
        # Process each detected person
        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = box
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # Update track history
            self.track_history[track_id].append((center_x, center_y))
            if len(self.track_history[track_id]) > 30:  # Keep last 30 points
                self.track_history[track_id].pop(0)
            
            # Check which zone the person is in
            current_zone = self._get_zone_for_point((center_x, center_y), zones)
            
            if current_zone:
                # Update zone occupancy
                self.zone_occupancy[current_zone] += 1
                frame_results["people_per_zone"][current_zone] = self.zone_occupancy[current_zone]
                
                # Update dwell time
                current_time = time.time()
                if track_id in self.last_seen:
                    time_spent = current_time - self.last_seen[track_id]
                    self.dwell_times[current_zone][track_id] += time_spent
                self.last_seen[track_id] = current_time
                
                # Update movement patterns
                if len(self.track_history[track_id]) > 1:
                    prev_point = self.track_history[track_id][-2]
                    movement_vector = (center_x - prev_point[0], center_y - prev_point[1])
                    if current_zone not in frame_results["movement_patterns"]:
                        frame_results["movement_patterns"][current_zone] = []
                    frame_results["movement_patterns"][current_zone].append({
                        "track_id": track_id,
                        "vector": movement_vector,
                        "timestamp": current_time
                    })
        
        # Update frame results
        frame_results["total_people"] = len(track_ids)
        
        # Calculate dwell times for the frame
        for zone, track_times in self.dwell_times.items():
            if track_times:
                frame_results["dwell_times"][zone] = sum(track_times.values()) / len(track_times)
        
        return frame_results
    
    def _get_zone_for_point(self, point: Tuple[float, float], zones: Dict[str, List[Tuple[int, int]]]) -> str:
        """
        Determine which zone a point belongs to.
        
        Args:
            point: (x, y) coordinates of the point
            zones: Dictionary of zone names and their polygon coordinates
            
        Returns:
            Name of the zone the point is in, or None if not in any zone
        """
        for zone_name, polygon in zones.items():
            if self._point_in_polygon(point, polygon):
                return zone_name
        return None
    
    def _point_in_polygon(self, point: Tuple[float, float], polygon: List[Tuple[int, int]]) -> bool:
        """
        Check if a point is inside a polygon using ray casting algorithm.
        """
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
            
        return inside 