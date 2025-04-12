import cv2
import numpy as np
import face_recognition
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.suspect import Suspect, SuspectImage, SuspectLocation
from app.models.alert import Alert
from app.core.database import SessionLocal
import json
import time

logger = logging.getLogger(__name__)

class SuspectTrackingService:
    def __init__(self):
        self.known_face_encodings: Dict[int, List[np.ndarray]] = {}
        self.known_face_ids: List[int] = []
        # Track recent detections for temporal consistency
        self.recent_detections: Dict[int, List[Tuple[float, Dict]]] = {}
        # Initialize face detection model
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # Load known faces with retry mechanism
        self._load_faces_attempts = 0
        self.load_known_faces()
    
    def _normalize_feature_vector(self, vector: np.ndarray) -> np.ndarray:
        """Normalize feature vector to unit length"""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def _serialize_feature_vector(self, feature_vector):
        """Convert a feature vector to a serialized format for database storage"""
        if feature_vector is None:
            return None
        
        # Always convert to a proper JSON string for consistent storage
        if isinstance(feature_vector, np.ndarray):
            return json.dumps(feature_vector.tolist())
        elif isinstance(feature_vector, list):
            return json.dumps(feature_vector)
        elif isinstance(feature_vector, str):
            # Verify it's valid JSON before returning
            try:
                json.loads(feature_vector)
                return feature_vector
            except:
                # If it's not valid JSON, try to convert it
                try:
                    return json.dumps(eval(feature_vector))
                except:
                    logger.error(f"Could not serialize feature vector: {feature_vector[:20]}...")
                    return None
        else:
            # For any other type, convert to list then JSON
            try:
                return json.dumps(list(feature_vector))
            except:
                logger.error(f"Failed to serialize feature vector of type: {type(feature_vector)}")
                return None
    
    def _deserialize_feature_vector(self, serialized_vector):
        """Convert a serialized feature vector back to a numpy array"""
        if serialized_vector is None:
            return None
        
        try:
            # Log the exact type and initial content for debugging
            logger.info(f"Deserializing vector of type {type(serialized_vector)}")
            if isinstance(serialized_vector, (str, bytes, memoryview)):
                sample = str(serialized_vector)[:50] + "..." if len(str(serialized_vector)) > 50 else str(serialized_vector)
                logger.info(f"Vector content sample: {sample}")
            
            # Handle memoryview objects
            if isinstance(serialized_vector, memoryview):
                serialized_vector = serialized_vector.tobytes().decode('utf-8')
            
            # Handle bytes
            if isinstance(serialized_vector, bytes):
                serialized_vector = serialized_vector.decode('utf-8')
            
            # Check if string is empty
            if not serialized_vector or serialized_vector.strip() == '':
                logger.warning("Empty feature vector string")
                return None
            
            # Handle JSON object case - if it's already a dict/list
            if isinstance(serialized_vector, (dict, list)):
                if isinstance(serialized_vector, dict) and 'data' in serialized_vector:
                    # Some databases store JSON as {'data': [...]}
                    vector_list = serialized_vector['data']
                else:
                    vector_list = serialized_vector
            else:
                # String case - handle the JSON string
                # First, make sure it's actually a string
                serialized_vector = str(serialized_vector)
                
                # Check if it starts with '[' and ends with ']' indicating a JSON array string
                if serialized_vector.strip().startswith('[') and serialized_vector.strip().endswith(']'):
                    try:
                        vector_list = json.loads(serialized_vector)
                    except json.JSONDecodeError as jde:
                        logger.error(f"JSON decode error for array string: {jde}")
                        # Try cleaning the string
                        clean_str = ''.join(c for c in serialized_vector if c.isprintable())
                        try:
                            vector_list = json.loads(clean_str)
                        except:
                            logger.error(f"Second JSON decode attempt failed for: {clean_str[:30]}...")
                            return None
                else:
                    # If it's not a proper JSON array string, it might be escaped or have extra quotes
                    try:
                        # Try some common cleanup patterns
                        # 1. Remove outer quotes if present
                        if (serialized_vector.startswith('"') and serialized_vector.endswith('"')) or \
                           (serialized_vector.startswith("'") and serialized_vector.endswith("'")):
                            serialized_vector = serialized_vector[1:-1]
                        
                        # 2. Try to load directly
                        vector_list = json.loads(serialized_vector)
                    except json.JSONDecodeError:
                        # 3. Try un-escaping string
                        try:
                            import ast
                            unescaped = ast.literal_eval(f'"{serialized_vector}"')
                            vector_list = json.loads(unescaped)
                        except:
                            logger.error(f"All string un-escaping attempts failed")
                            return None
            
            # Validate that it's a list with proper dimensions
            if not isinstance(vector_list, list):
                logger.warning(f"Deserialized feature vector is not a list: {type(vector_list)}")
                return None
            
            # Check if the list has proper dimensions
            if len(vector_list) != 128:
                logger.warning(f"Feature vector has unexpected dimensions: {len(vector_list)}")
                if len(vector_list) > 0 and isinstance(vector_list[0], list) and len(vector_list[0]) == 128:
                    # Handle nested list case - some serializers might nest the array
                    vector_list = vector_list[0]
                    logger.info("Extracted nested feature vector with correct dimensions")
                else:
                    # If dimensions are still wrong, return None
                    return None
            
            # Convert to numpy array
            array = np.array(vector_list, dtype=np.float64)
            
            # Verify array has expected shape and contains valid values
            if array.shape != (128,) or not np.isfinite(array).all():
                logger.warning(f"Invalid array shape or values: shape={array.shape}, valid={np.isfinite(array).all()}")
                return None
                
            return array
        except Exception as e:
            logger.error(f"Error deserializing feature vector: {e}")
            logger.error(f"Vector type: {type(serialized_vector)}")
            if isinstance(serialized_vector, (str, bytes, memoryview)):
                logger.error(f"Vector preview: {str(serialized_vector)[:50]}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def load_known_faces(self) -> None:
        """Load all known face encodings from the database with better error handling"""
        logger.info("Loading known faces from database")
        db = SessionLocal()
        try:
            # Reset data structures
            self.known_face_encodings = {}
            self.known_face_ids = []
            self.recent_detections = {}
            
            # Query all active suspects
            suspects = db.query(Suspect).filter(Suspect.is_active == True).all()
            logger.info(f"Found {len(suspects)} active suspects")
            
            # Count loaded encodings for diagnostics
            loaded_encodings = 0
            
            for suspect in suspects:
                self.known_face_ids.append(suspect.id)
                self.known_face_encodings[suspect.id] = []
                self.recent_detections[suspect.id] = []
                
                # Load images for this suspect
                images = db.query(SuspectImage).filter(SuspectImage.suspect_id == suspect.id).all()
                logger.info(f"Suspect ID {suspect.id} ({suspect.name}) has {len(images)} images")
                
                for idx, image in enumerate(images):
                    try:
                        logger.info(f"  Image {idx+1}: ID={image.id}")
                        
                        # Check if feature vector exists
                        if image.feature_vector is None:
                            logger.warning(f"Image {image.id} has no feature vector")
                            continue
                        
                        # Convert the stored feature vector back to a numpy array
                        feature_vector = self._deserialize_feature_vector(image.feature_vector)
                        
                        if feature_vector is not None:
                            # Validate dimensions (face_recognition uses 128-dim vectors)
                            if len(feature_vector) == 128:
                                self.known_face_encodings[suspect.id].append(feature_vector)
                                loaded_encodings += 1
                                logger.info(f"Loaded face encoding for suspect {suspect.id}, image {image.id}")
                            else:
                                logger.warning(f"Invalid feature vector dimensions for image {image.id}: expected 128, got {len(feature_vector)}")
                        else:
                            logger.warning(f"Failed to deserialize feature vector for image {image.id}")
                    except Exception as e:
                        logger.error(f"Error loading face encoding for image {image.id}: {str(e)}")
                        continue
            
            # Log summary
            total_encodings = sum(len(encodings) for encodings in self.known_face_encodings.values())
            logger.info(f"Loaded {len(self.known_face_ids)} suspects with {total_encodings} total face encodings")
            
            # Check if we actually loaded any encodings
            if total_encodings == 0:
                logger.warning("No feature vectors were loaded. Face detection will not work.")
                
                # Track retry attempts
                self._load_faces_attempts += 1
                if self._load_faces_attempts <= 3:
                    logger.info(f"Will retry loading faces (attempt {self._load_faces_attempts})")
            else:
                # Reset retry counter on success
                self._load_faces_attempts = 0
                
        except Exception as e:
            logger.error(f"Error loading known faces: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            db.close()
    
    def _detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Enhanced face detection with better error handling"""
        try:
            # Input validation
            if frame is None or frame.size == 0:
                logger.warning("Empty frame received")
                return []

            # Convert to grayscale if needed
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame.copy()

            # Ensure image is 8-bit
            if gray.dtype != np.uint8:
                gray = (gray * 255).astype(np.uint8)

            # Ensure minimum size
            min_size = 100
            if gray.shape[0] < min_size or gray.shape[1] < min_size:
                gray = cv2.resize(gray, (min_size, min_size))

            # Apply histogram equalization to improve contrast
            gray = cv2.equalizeHist(gray)

            face_locations = []
            
            try:
                # Try OpenCV's cascade detector first with conservative parameters
                faces = self.face_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.1,  # Conservative scale factor
                    minNeighbors=5,   # More strict neighbor requirement
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                if len(faces) > 0:
                    for (x, y, w, h) in faces:
                        # Convert to face_recognition format (top, right, bottom, left)
                        face_locations.append((y, x + w, y + h, x))
            except Exception as e:
                logger.warning(f"OpenCV cascade detection failed: {str(e)}")

            # If OpenCV detection failed or found no faces, try face_recognition's HOG detector
            if not face_locations:
                logger.info("Falling back to HOG-based detector")
                try:
                    face_locations = face_recognition.face_locations(frame, model="hog")
                except Exception as e:
                    logger.warning(f"HOG-based detection failed: {str(e)}")
                    return []

            # Remove duplicates while preserving order
            if face_locations:
                face_locations = list(dict.fromkeys(face_locations))
                logger.debug(f"Detected {len(face_locations)} faces")
            
            return face_locations
            
        except Exception as e:
            logger.error(f"Error in face detection: {str(e)}")
            return []
    
    def _align_face(self, frame: np.ndarray, face_location: Tuple[int, int, int, int]) -> np.ndarray:
        """Align face using facial landmarks"""
        try:
            top, right, bottom, left = face_location
            face_image = frame[top:bottom, left:right]
            
            # Get facial landmarks
            landmarks = face_recognition.face_landmarks(face_image)
            if not landmarks:
                return face_image
            
            # Use eyes for alignment
            left_eye = np.mean(landmarks[0]['left_eye'], axis=0)
            right_eye = np.mean(landmarks[0]['right_eye'], axis=0)
            
            # Calculate angle for alignment
            dY = right_eye[1] - left_eye[1]
            dX = right_eye[0] - left_eye[0]
            angle = np.degrees(np.arctan2(dY, dX))
            
            # Rotate image
            center = ((left + right) // 2, (top + bottom) // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            aligned_face = cv2.warpAffine(face_image, M, (face_image.shape[1], face_image.shape[0]))
            
            return aligned_face
        except Exception as e:
            logger.warning(f"Face alignment failed: {str(e)}")
            return frame[top:bottom, left:right]
    
    def detect_suspects(self, frame: np.ndarray, camera_id: str) -> List[Dict]:
        """Enhanced suspect detection with simplified face recognition"""
        try:
            # Validate loaded suspects
            if not self.known_face_ids or all(len(encodings) == 0 for encodings in self.known_face_encodings.values()):
                logger.warning("No suspects loaded. Attempting to reload.")
                self.load_known_faces()
                if not self.known_face_ids:
                    logger.error("Still no suspects available after reload.")
                    return []
            
            # Ensure frame is a valid RGB image
            if frame is None or frame.size == 0 or len(frame.shape) != 3:
                logger.warning("Invalid frame format")
                return []
            
            # Convert to RGB (face_recognition requires RGB format)
            if frame.dtype != np.uint8:
                frame = (frame * 255).astype(np.uint8)
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Simple face detection using face_recognition
            try:
                logger.debug("Detecting faces in frame")
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                if not face_locations:
                    logger.debug(f"No faces detected in frame from camera {camera_id}")
                    return []
                
                logger.debug(f"Detected {len(face_locations)} faces")
                
                # Get face encodings safely
                face_encodings = []
                try:
                    # This is the corrected call to face_encodings with proper arguments
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    logger.debug(f"Generated {len(face_encodings)} face encodings")
                except Exception as e:
                    logger.error(f"Error generating face encodings: {str(e)}")
                    return []
                
                # No faces encoded
                if not face_encodings:
                    logger.warning("Failed to encode faces")
                    return []
                
                results = []
                for i, face_encoding in enumerate(face_encodings):
                    try:
                        # Get corresponding face location
                        face_location = face_locations[i]
                        
                        # Normalize face encoding
                        face_encoding = self._normalize_feature_vector(face_encoding)
                        
                        # Find best match
                        best_match_id = None
                        best_distance = 1.0  # Initialize with max distance
                        
                        # Constant threshold for matching
                        threshold = 0.6  # Lower means stricter matching
                        
                        # Compare with known faces
                        for suspect_id, known_encodings in self.known_face_encodings.items():
                            if not known_encodings:
                                continue
                                
                            try:
                                # Calculate distances to all encodings for this suspect
                                distances = face_recognition.face_distance(known_encodings, face_encoding)
                                min_dist = min(distances)
                                
                                # Update best match if this is better
                                if min_dist < best_distance and min_dist < threshold:
                                    best_distance = min_dist
                                    best_match_id = suspect_id
                            except Exception as e:
                                logger.warning(f"Error comparing face distance: {str(e)}")
                        
                        # If we found a match
                        if best_match_id is not None:
                            confidence = 1.0 - best_distance
                            detection = {
                                "suspect_id": best_match_id,
                                "confidence": confidence,
                                "location": {
                                    "top": face_location[0],
                                    "right": face_location[1],
                                    "bottom": face_location[2],
                                    "left": face_location[3]
                                }
                            }
                            
                            # Record detection
                            current_time = time.time()
                            if best_match_id in self.recent_detections:
                                self.recent_detections[best_match_id].append((current_time, detection))
                                # Keep only recent detections
                                self.recent_detections[best_match_id] = [
                                    (t, d) for t, d in self.recent_detections[best_match_id]
                                    if current_time - t <= 30
                                ]
                            
                            results.append(detection)
                            logger.info(f"Matched suspect {best_match_id} with confidence {confidence:.2f}")
                    except Exception as e:
                        logger.warning(f"Error processing face: {str(e)}")
                
                return results
            except Exception as e:
                logger.error(f"Error in face detection: {str(e)}")
                return []
            
        except Exception as e:
            logger.error(f"Error detecting suspects: {str(e)}")
            return []
    
    def process_image(self, image_path: str) -> Optional[np.ndarray]:
        """Process an image to extract face encodings"""
        logger.info(f"Processing image: {image_path}")
        
        # Validate image path
        if not image_path:
            logger.error("No image path provided")
            return None
        
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        try:
            # Load the image
            try:
                image = face_recognition.load_image_file(image_path)
                if image is None or image.size == 0:
                    logger.error(f"Failed to load image: {image_path}")
                    return None
                
                logger.info(f"Loaded image with dimensions: {image.shape}")
            except Exception as e:
                logger.error(f"Error loading image {image_path}: {str(e)}")
                return None
            
            # Find all face locations in the image
            try:
                face_locations = face_recognition.face_locations(image)
                logger.info(f"Found {len(face_locations)} faces in the image")
                
                if not face_locations:
                    logger.warning(f"No faces found in image: {image_path}")
                    return None
            except Exception as e:
                logger.error(f"Error detecting faces in image {image_path}: {str(e)}")
                return None
            
            # Get face encoding for the face
            try:
                face_encodings = face_recognition.face_encodings(image, [face_locations[0]])
                
                if not face_encodings or len(face_encodings) == 0:
                    logger.warning(f"Failed to generate encoding for face in image: {image_path}")
                    return None
                
                # Validate encoding
                face_encoding = face_encodings[0]
                if not isinstance(face_encoding, np.ndarray):
                    logger.error(f"Encoding is not a numpy array: {type(face_encoding)}")
                    return None
                
                if len(face_encoding) != 128:
                    logger.error(f"Face encoding has wrong dimensions: {len(face_encoding)}")
                    return None
                
                # Make sure the encoding contains valid floats
                if not np.isfinite(face_encoding).all():
                    logger.error("Face encoding contains NaN or infinite values")
                    return None
                
                # Return the face encoding as a numpy array
                logger.info(f"Successfully generated valid face encoding with shape {face_encoding.shape}")
                return face_encoding
            except Exception as e:
                logger.error(f"Error generating face encoding for image {image_path}: {str(e)}")
                return None
        
        except Exception as e:
            logger.error(f"Unexpected error processing image {image_path}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def add_suspect_image(self, suspect_id: int, image_path: str, db: Session) -> bool:
        """Add a new image for a suspect and process it for facial recognition"""
        try:
            # Process the image
            face_encoding = self.process_image(image_path)
            if face_encoding is None:
                logger.error(f"Failed to process image: {image_path}")
                return False
            
            # Create thumbnail
            thumbnail_path = self._create_thumbnail(image_path)
            
            # Create new image record
            feature_vector = self._serialize_feature_vector(face_encoding)
            logger.info(f"Generated feature vector of length: {len(feature_vector)}")
            
            new_image = SuspectImage(
                suspect_id=suspect_id,
                image_path=image_path,
                thumbnail_path=thumbnail_path,
                feature_vector=feature_vector,
                confidence_score=1.0,
                capture_date=datetime.now(),
                source="upload"
            )
            
            db.add(new_image)
            db.commit()
            
            # Update in-memory cache
            if suspect_id not in self.known_face_encodings:
                self.known_face_encodings[suspect_id] = []
                self.known_face_ids.append(suspect_id)
            self.known_face_encodings[suspect_id].append(face_encoding)
            
            logger.info(f"Successfully added image for suspect ID: {suspect_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding suspect image: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            db.rollback()
            return False
    
    def _create_thumbnail(self, image_path: str) -> str:
        """Create a thumbnail version of the image"""
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return ""
                
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Failed to read image for thumbnail: {image_path}")
                return ""
                
            height, width = img.shape[:2]
            scale = 200 / max(height, width)
            thumbnail = cv2.resize(img, None, fx=scale, fy=scale)
            
            # Save thumbnail
            dirname = os.path.dirname(image_path)
            basename = os.path.basename(image_path)
            name_part, ext = os.path.splitext(basename)
            thumb_path = os.path.join(dirname, f"{name_part}_thumb{ext}")
            
            cv2.imwrite(thumb_path, thumbnail)
            logger.info(f"Created thumbnail at: {thumb_path}")
            return thumb_path
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return ""
    
    def track_suspect_location(self, suspect_id: int, camera_id: str, 
                             coordinates: Dict, confidence: float, 
                             frame_number: int, db: Session) -> None:
        """Record a suspect's location"""
        try:
            location = SuspectLocation(
                suspect_id=suspect_id,
                camera_id=camera_id,
                coordinates=coordinates,
                confidence=confidence,
                frame_number=frame_number
            )
            
            db.add(location)
            db.commit()
        except Exception as e:
            logger.error(f"Error tracking suspect location: {str(e)}")
            db.rollback()
    
    def generate_alert(self, suspect_id: int, camera_id: str, 
                      confidence: float, snapshot_path: str, 
                      db: Session) -> None:
        """Generate an alert for a detected suspect"""
        try:
            alert = Alert(
                alert_type="suspect_detected",
                severity=3,  # Medium priority
                track_id=str(suspect_id),
                description=f"Suspect {suspect_id} detected on {camera_id} with confidence {confidence:.2f}",
                snapshot_path=snapshot_path,
                suspect_id=suspect_id
            )
            
            logger.info(f"Attempting to add alert to session: {alert.__dict__}")
            db.add(alert)
            logger.info(f"Alert added to session. Attempting to commit.")
            db.commit()
            logger.info(f"Alert committed successfully! ID: {alert.id}")
            
            # Broadcast the alert via WebSocket
            # (Need to implement broadcasting logic if not already done)
            # Example: await broadcast_alert(alert)
            
        except Exception as e:
            logger.error(f"Error generating alert: {str(e)}")
            import traceback
            logger.error(traceback.format_exc()) # Log full traceback
            try:
                db.rollback()
                logger.info("Database rollback successful after alert generation error.")
            except Exception as rb_e:
                logger.error(f"Database rollback failed after alert generation error: {rb_e}")

# Create singleton instance
suspect_tracking_service = SuspectTrackingService()

# Add diagnostic and maintenance functions
def reload_suspect_service():
    """Force reload of the suspect tracking service"""
    logger.info("Manual reload of suspect tracking service initiated")
    suspect_tracking_service.load_known_faces()
    
    # Check if reload was successful
    suspect_count = len(suspect_tracking_service.known_face_ids)
    
    encoding_count = sum(len(encodings) for encodings in 
                          suspect_tracking_service.known_face_encodings.values())
                          
    status = {
        "suspect_count": suspect_count,
        "encoding_count": encoding_count,
        "suspects": {}
    }
    
    # Log details for each suspect
    for suspect_id in suspect_tracking_service.known_face_ids:
        encodings = suspect_tracking_service.known_face_encodings.get(suspect_id, [])
        status["suspects"][suspect_id] = {
            "encoding_count": len(encodings),
            "encoding_shapes": [e.shape if isinstance(e, np.ndarray) else None for e in encodings]
        }
    
    logger.info(f"Service reload status: {status}")
    return status 