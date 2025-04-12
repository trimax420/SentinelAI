import os
import logging
import json
import numpy as np
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.suspect import Suspect, SuspectImage
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_feature_vector(vector):
    """Check if a feature vector is valid"""
    try:
        # If it's a string, try to parse as JSON
        if isinstance(vector, (str, bytes, memoryview)):
            if isinstance(vector, memoryview):
                vector = vector.tobytes().decode('utf-8')
            if isinstance(vector, bytes):
                vector = vector.decode('utf-8')
                
            # Check if string is empty
            if not vector or vector.strip() == '':
                return False
                
            # Parse JSON
            parsed = json.loads(vector)
            
            # Check if it's a list of the right length
            if not isinstance(parsed, list):
                return False
                
            # For face recognition, we expect 128-dimensional vectors
            if len(parsed) != 128:
                logger.warning(f"Vector has unexpected dimensions: {len(parsed)}")
                
            # Check if all values are finite numbers
            for val in parsed:
                if not isinstance(val, (int, float)) or not np.isfinite(val):
                    return False
                    
            return True
        elif isinstance(vector, (list, np.ndarray)):
            # Check if it's a list/array of the right length
            if len(vector) != 128:
                logger.warning(f"Vector has unexpected dimensions: {len(vector)}")
                
            # Check if all values are finite numbers
            for val in vector:
                if not isinstance(val, (int, float)) or not np.isfinite(val):
                    return False
                    
            return True
        else:
            # Unknown type
            return False
    except Exception as e:
        logger.error(f"Error validating feature vector: {str(e)}")
        return False

def fix_feature_vector(vector):
    """Attempt to fix an invalid feature vector"""
    try:
        # If it's None or empty, we can't fix it
        if vector is None:
            return None
            
        # If already valid, return as is
        if is_valid_feature_vector(vector):
            return vector
            
        # Try to convert to a string if it's bytes or memoryview
        if isinstance(vector, (memoryview, bytes)):
            try:
                vector_str = vector.tobytes().decode('utf-8') if isinstance(vector, memoryview) else vector.decode('utf-8')
                
                # Try to parse as JSON
                try:
                    parsed = json.loads(vector_str)
                    if isinstance(parsed, list) and len(parsed) == 128:
                        return json.dumps(parsed)
                except json.JSONDecodeError:
                    pass
                    
                # Try to parse as a literal
                try:
                    parsed = eval(vector_str)
                    if isinstance(parsed, (list, np.ndarray)) and len(parsed) == 128:
                        return json.dumps(list(parsed))
                except:
                    pass
            except:
                pass
                
        # If it's a numpy array, convert to list and then to JSON
        if isinstance(vector, np.ndarray) and len(vector) == 128:
            return json.dumps(vector.tolist())
            
        # If it's a list of the right length, convert to JSON
        if isinstance(vector, list) and len(vector) == 128:
            return json.dumps(vector)
            
        # We couldn't fix it
        return None
    except Exception as e:
        logger.error(f"Error fixing feature vector: {str(e)}")
        return None

def validate_and_fix_feature_vectors():
    """Validate and fix feature vectors in the database"""
    db = SessionLocal()
    try:
        # Count statistics
        total_images = 0
        valid_vectors = 0
        fixed_vectors = 0
        unfixable_vectors = 0
        
        # Process all suspect images
        suspect_images = db.query(SuspectImage).all()
        total_images = len(suspect_images)
        logger.info(f"Found {total_images} suspect images")
        
        for image in suspect_images:
            try:
                logger.info(f"Processing image ID {image.id}")
                
                # Skip if no feature vector
                if image.feature_vector is None:
                    logger.warning(f"Image ID {image.id} has no feature vector")
                    unfixable_vectors += 1
                    continue
                
                # Check if feature vector is valid
                if is_valid_feature_vector(image.feature_vector):
                    logger.info(f"Image ID {image.id} has a valid feature vector")
                    valid_vectors += 1
                    continue
                    
                # Try to fix the feature vector
                logger.warning(f"Image ID {image.id} has an invalid feature vector")
                fixed_vector = fix_feature_vector(image.feature_vector)
                
                if fixed_vector is not None:
                    # Update the database
                    image.feature_vector = fixed_vector
                    db.commit()
                    logger.info(f"Fixed feature vector for image ID {image.id}")
                    fixed_vectors += 1
                else:
                    logger.error(f"Could not fix feature vector for image ID {image.id}")
                    unfixable_vectors += 1
            except Exception as e:
                logger.error(f"Error processing image ID {image.id}: {str(e)}")
                unfixable_vectors += 1
                continue
        
        # Print statistics
        logger.info("--- Feature Vector Validation Summary ---")
        logger.info(f"Total images: {total_images}")
        logger.info(f"Valid vectors: {valid_vectors}")
        logger.info(f"Fixed vectors: {fixed_vectors}")
        logger.info(f"Unfixable vectors: {unfixable_vectors}")
        
    except Exception as e:
        logger.error(f"Error validating feature vectors: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting feature vector validation")
    validate_and_fix_feature_vectors()
    logger.info("Feature vector validation complete") 