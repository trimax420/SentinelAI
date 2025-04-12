import os
import sys
import logging
import json
import face_recognition
import cv2
import numpy as np
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.suspect import Suspect, SuspectImage
from datetime import datetime
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_suspect_storage():
    """Debug issues with suspect image storage"""
    db = SessionLocal()
    try:
        # 1. Check database configuration
        logger.info("Checking database configuration...")
        try:
            # Get engine metadata
            from app.core.database import engine
            inspector = db.inspect(engine)
            tables = inspector.get_table_names()
            logger.info(f"Database tables: {', '.join(tables)}")
            
            # Check if suspect_images table exists
            if 'suspect_images' in tables:
                columns = inspector.get_columns('suspect_images')
                column_names = [col['name'] for col in columns]
                logger.info(f"suspect_images columns: {', '.join(column_names)}")
                
                # Check if feature_vector column exists and its type
                feature_vector_col = next((col for col in columns if col['name'] == 'feature_vector'), None)
                if feature_vector_col:
                    logger.info(f"feature_vector column type: {feature_vector_col['type']}")
                else:
                    logger.error("feature_vector column not found!")
            else:
                logger.error("suspect_images table not found!")
        except Exception as e:
            logger.error(f"Error inspecting database: {str(e)}")
        
        # 2. Check all suspects
        suspects = db.query(Suspect).all()
        logger.info(f"Found {len(suspects)} total suspects")
        
        for suspect in suspects:
            logger.info(f"Suspect {suspect.id}: {suspect.name}, Active: {suspect.is_active}")
            
            # 3. Check images for each suspect
            images = db.query(SuspectImage).filter(SuspectImage.suspect_id == suspect.id).all()
            logger.info(f"  Found {len(images)} images for suspect {suspect.id}")
            
            for idx, image in enumerate(images):
                logger.info(f"  Image {idx+1}: ID={image.id}")
                logger.info(f"    Path: {image.image_path}")
                logger.info(f"    Created: {image.created_at}")
                
                # Check if file exists
                if image.image_path and os.path.exists(image.image_path):
                    file_size = os.path.getsize(image.image_path)
                    logger.info(f"    File exists: {file_size} bytes")
                    
                    # Try to load the image
                    try:
                        img = cv2.imread(image.image_path)
                        if img is not None:
                            logger.info(f"    Image dimensions: {img.shape}")
                        else:
                            logger.error(f"    Failed to load image with OpenCV")
                    except Exception as e:
                        logger.error(f"    Error loading image: {str(e)}")
                else:
                    logger.error(f"    File does not exist: {image.image_path}")
                
                # Check feature vector
                if image.feature_vector:
                    try:
                        if isinstance(image.feature_vector, bytes):
                            vector_str = image.feature_vector.decode('utf-8')
                        else:
                            vector_str = image.feature_vector
                            
                        logger.info(f"    Feature vector length: {len(vector_str)}")
                        
                        # Try parsing as JSON
                        try:
                            vector_data = json.loads(vector_str)
                            if isinstance(vector_data, list):
                                logger.info(f"    Vector is a valid JSON array of length {len(vector_data)}")
                                
                                # Check dimensions
                                if len(vector_data) != 128:
                                    logger.warning(f"    Unusual vector dimensions: {len(vector_data)}, expected 128")
                            else:
                                logger.error(f"    Feature vector not a list: {type(vector_data)}")
                        except json.JSONDecodeError:
                            logger.error(f"    Feature vector not valid JSON")
                            logger.error(f"    First 100 chars: {vector_str[:100]}...")
                            
                    except Exception as e:
                        logger.error(f"    Error parsing feature vector: {str(e)}")
                else:
                    logger.error(f"    No feature vector stored")
        
        # 4. Try to create a test image and feature vector
        logger.info("Testing image creation and feature vector generation...")
        
        # Create a simple test image
        test_dir = os.path.join("data", "test")
        os.makedirs(test_dir, exist_ok=True)
        test_image_path = os.path.join(test_dir, f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        
        # Create a solid color test image
        test_img = np.ones((200, 200, 3), dtype=np.uint8) * np.array([50, 100, 200], dtype=np.uint8)
        cv2.imwrite(test_image_path, test_img)
        logger.info(f"Created test image at {test_image_path}")
        
        # Create a static 128-dimensional feature vector
        feature_vector = np.random.randn(128).astype(np.float64)
        # Normalize
        norm = np.linalg.norm(feature_vector)
        if norm > 0:
            feature_vector = feature_vector / norm
            
        # Serialize to JSON
        feature_json = json.dumps(feature_vector.tolist())
        logger.info(f"Created test feature vector, length: {len(feature_json)}")
        
        # 5. Test database storage
        logger.info("Testing database storage...")
        
        # Create a test suspect if none exists
        test_suspect = db.query(Suspect).filter(Suspect.name == "TEST_DEBUG").first()
        if not test_suspect:
            test_suspect = Suspect(
                name="TEST_DEBUG",
                physical_description="Test suspect for debugging",
                is_active=True
            )
            db.add(test_suspect)
            db.flush()
            logger.info(f"Created test suspect with ID: {test_suspect.id}")
        else:
            logger.info(f"Using existing test suspect with ID: {test_suspect.id}")
        
        # Create test image record
        test_image = SuspectImage(
            suspect_id=test_suspect.id,
            image_path=test_image_path,
            feature_vector=feature_json,
            confidence_score=1.0,
            capture_date=datetime.now(),
            source="debug_test"
        )
        
        db.add(test_image)
        db.commit()
        logger.info(f"Added test image with ID: {test_image.id}")
        
        # Verify it was stored correctly
        stored_image = db.query(SuspectImage).filter(SuspectImage.id == test_image.id).first()
        if stored_image:
            logger.info("Successfully retrieved test image from database")
            
            if stored_image.feature_vector:
                logger.info(f"Feature vector stored successfully, length: {len(stored_image.feature_vector)}")
                
                # Try parsing
                try:
                    vector_data = json.loads(stored_image.feature_vector)
                    logger.info(f"Successfully parsed feature vector: length={len(vector_data)}")
                except Exception as e:
                    logger.error(f"Error parsing stored feature vector: {str(e)}")
            else:
                logger.error("Feature vector not stored properly")
        else:
            logger.error("Failed to retrieve test image from database")
            
        logger.info("Debug complete")
                
    except Exception as e:
        logger.error(f"Error during debugging: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting suspect image storage debugging")
    debug_suspect_storage()
    logger.info("Debug complete") 