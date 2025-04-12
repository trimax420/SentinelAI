import os
import sys
import logging
import face_recognition
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.suspect import Suspect, SuspectImage
import cv2
import numpy as np
import json
from datetime import datetime
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_suspect(name: str, image_path: str, aliases: list = None, description: str = None):
    """Register a new suspect with their face image"""
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return False

    db = SessionLocal()

    try:
        logger.info(f"Starting registration for {name} with image {image_path}")
        
        # Step 1: Create suspect record
        suspect = Suspect(
            name=name,
            aliases=aliases,
            physical_description=description,
            is_active=True
        )
        db.add(suspect)
        db.flush()  # Get the ID without committing
        logger.info(f"Created suspect record with ID: {suspect.id}")
        
        # Step 2: Process the image for face detection
        try:
            # Load image with face_recognition
            logger.info(f"Loading image: {image_path}")
            image = face_recognition.load_image_file(image_path)
            logger.info(f"Image loaded successfully, shape: {image.shape}")
            
            # Detect faces
            logger.info("Detecting faces...")
            face_locations = face_recognition.face_locations(image, model="hog")
            logger.info(f"Detected {len(face_locations)} faces")
            
            if not face_locations:
                logger.error("No faces detected in the image")
                db.rollback()
                return False
            
            # Get face encodings
            logger.info("Generating face encodings...")
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if not face_encodings or len(face_encodings) == 0:
                logger.error("Failed to generate face encodings")
                db.rollback()
                return False
            
            logger.info("Successfully generated face encodings")
            
            # Get the first face encoding
            face_encoding = face_encodings[0]
            
            # Normalize the vector
            norm = np.linalg.norm(face_encoding)
            if norm > 0:
                face_encoding = face_encoding / norm
                
            # Serialize to JSON
            feature_vector = json.dumps(face_encoding.tolist())
            logger.info(f"Feature vector created, length: {len(feature_vector)}")
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            logger.error(traceback.format_exc())
            db.rollback()
            return False
            
        # Step 3: Create thumbnail
        thumbnail_path = ""
        try:
            # Create a thumbnail from the image
            img = cv2.imread(image_path)
            height, width = img.shape[:2]
            scale = 200 / max(height, width)
            thumbnail = cv2.resize(img, None, fx=scale, fy=scale)
            
            # Create thumbnails directory
            dirname = os.path.dirname(image_path)
            basename = os.path.basename(image_path)
            name_part, ext = os.path.splitext(basename)
            thumbnail_path = os.path.join(dirname, f"{name_part}_thumb{ext}")
            
            # Save thumbnail
            cv2.imwrite(thumbnail_path, thumbnail)
            logger.info(f"Created thumbnail at: {thumbnail_path}")
            
        except Exception as e:
            logger.warning(f"Failed to create thumbnail: {str(e)}")
            # Continue anyway, thumbnail is not critical
            
        # Step 4: Create suspect image record
        try:
            # Get absolute path
            abs_image_path = os.path.abspath(image_path)
            logger.info(f"Using absolute image path: {abs_image_path}")
            
            image_record = SuspectImage(
                suspect_id=suspect.id,
                image_path=abs_image_path,
                thumbnail_path=thumbnail_path if thumbnail_path else None,
                feature_vector=feature_vector,
                confidence_score=1.0,
                capture_date=datetime.now(),
                source="manual_registration",
                is_primary=True
            )
            db.add(image_record)
            
            # Log details before commit
            logger.info(f"Added image record for suspect ID: {suspect.id}")
            
            # Commit transaction
            db.commit()
            logger.info(f"Successfully registered suspect: {name} with ID: {suspect.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating suspect image record: {str(e)}")
            logger.error(traceback.format_exc())
            db.rollback()
            return False

    except Exception as e:
        logger.error(f"Error registering suspect: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m app.scripts.register_suspect \"John Doe\" \"path/to/image.jpg\" \"alias1,alias2\" \"Description\"")
        sys.exit(1)

    name = sys.argv[1]
    image_path = sys.argv[2]
    aliases = sys.argv[3].split(',') if len(sys.argv) > 3 else None
    description = sys.argv[4] if len(sys.argv) > 4 else None

    success = register_suspect(name, image_path, aliases, description)
    if success:
        print(f"Successfully registered suspect: {name}")
        print("You can now test face detection with this suspect")
    else:
        print("Failed to register suspect")
        sys.exit(1) 