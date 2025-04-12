import logging
import json
import numpy as np
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.suspect import SuspectImage
from app.services.suspect_tracking import suspect_tracking_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_feature_vectors():
    """Fix feature vectors in the database to ensure proper JSON strings"""
    db = SessionLocal()
    try:
        # Get all images
        images = db.query(SuspectImage).all()
        logger.info(f"Found {len(images)} suspect images")
        
        fixed_count = 0
        error_count = 0
        
        for image in images:
            try:
                # Skip if no feature vector
                if image.feature_vector is None:
                    logger.info(f"Image {image.id}: No feature vector")
                    continue
                
                logger.info(f"Image {image.id}: Processing feature vector")
                logger.info(f"  Type: {type(image.feature_vector)}")
                if isinstance(image.feature_vector, (str, bytes, memoryview)):
                    preview = str(image.feature_vector)[:50] + "..." if len(str(image.feature_vector)) > 50 else str(image.feature_vector)
                    logger.info(f"  Content: {preview}")
                
                # Try to deserialize to validate
                feature_vector = suspect_tracking_service._deserialize_feature_vector(image.feature_vector)
                
                # If we can deserialize it, everything is fine
                if feature_vector is not None and isinstance(feature_vector, np.ndarray) and len(feature_vector) == 128:
                    logger.info(f"  → Feature vector is valid, ensuring proper JSON format")
                    
                    # Re-serialize to ensure consistent format
                    json_str = json.dumps(feature_vector.tolist())
                    
                    # Update the database
                    image.feature_vector = json_str
                    db.commit()
                    fixed_count += 1
                    logger.info(f"  ✓ Updated to proper JSON format")
                else:
                    logger.warning(f"  ✗ Could not deserialize feature vector")
                    error_count += 1
                    
                    # If feature vector path exists, try to regenerate
                    if image.image_path and os.path.exists(image.image_path):
                        logger.info(f"  → Attempting to regenerate from image file")
                        try:
                            new_vector = suspect_tracking_service.process_image(image.image_path)
                            if new_vector is not None:
                                json_str = json.dumps(new_vector.tolist())
                                image.feature_vector = json_str
                                db.commit()
                                logger.info(f"  ✓ Successfully regenerated feature vector")
                                fixed_count += 1
                                error_count -= 1
                            else:
                                logger.warning(f"  ✗ Failed to regenerate feature vector")
                        except Exception as e:
                            logger.error(f"  ✗ Error regenerating: {str(e)}")
                    else:
                        logger.warning(f"  ✗ Image file not found, cannot regenerate")
            
            except Exception as e:
                logger.error(f"Error processing image {image.id}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                error_count += 1
        
        logger.info(f"Fixed {fixed_count} feature vectors, {error_count} errors")
        
        # Reload suspect tracking service
        suspect_tracking_service.load_known_faces()
        
    except Exception as e:
        logger.error(f"Error fixing feature vectors: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    import os
    fix_feature_vectors() 