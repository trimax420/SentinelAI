import os
import sys
import logging
import json
import numpy as np
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.suspect import Suspect, SuspectImage
from app.services.suspect_tracking import suspect_tracking_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_suspect_embeddings(suspect_id=None):
    """Check if suspects have valid face embeddings stored in the database"""
    db = SessionLocal()
    
    try:
        # Get query for suspects
        query = db.query(Suspect)
        if suspect_id:
            query = query.filter(Suspect.id == suspect_id)
            
        suspects = query.all()
        logger.info(f"Found {len(suspects)} suspects to check")
        
        for suspect in suspects:
            logger.info(f"Checking suspect ID: {suspect.id} - {suspect.name}")
            
            # Get images for this suspect
            images = db.query(SuspectImage).filter(SuspectImage.suspect_id == suspect.id).all()
            logger.info(f"  Suspect has {len(images)} images")
            
            if not images:
                logger.warning(f"  No images found for suspect {suspect.id}")
                continue
                
            for idx, image in enumerate(images):
                logger.info(f"  Image {idx+1}: ID={image.id}, Path={image.image_path}")
                
                # Check if image file exists
                if not image.image_path or not os.path.exists(image.image_path):
                    logger.error(f"  Image file missing: {image.image_path}")
                    continue
                    
                # Check if feature vector exists
                if not image.feature_vector:
                    logger.error(f"  No feature vector for image {image.id}")
                    continue
                
                # Try to parse feature vector
                try:
                    if isinstance(image.feature_vector, bytes):
                        vector_str = image.feature_vector.decode('utf-8')
                    else:
                        vector_str = image.feature_vector
                        
                    # Try parsing as JSON
                    try:
                        vector_data = json.loads(vector_str)
                        
                        if isinstance(vector_data, list):
                            # Convert to numpy array
                            vector = np.array(vector_data)
                            logger.info(f"  Feature vector valid: shape={vector.shape}, type={type(vector)}")
                            
                            # Check dimensions
                            if vector.shape[0] != 128:
                                logger.warning(f"  Unusual vector dimensions: {vector.shape}")
                        else:
                            logger.error(f"  Feature vector not a list: {type(vector_data)}")
                            
                    except json.JSONDecodeError:
                        logger.error(f"  Feature vector not valid JSON")
                        
                except Exception as e:
                    logger.error(f"  Error parsing feature vector: {str(e)}")
                
                # Try recreating embedding from the image
                try:
                    logger.info(f"  Attempting to regenerate embedding from image...")
                    new_embedding = suspect_tracking_service.process_image(image.image_path)
                    
                    if new_embedding is not None:
                        logger.info(f"  Successfully regenerated embedding: shape={new_embedding.shape}")
                        
                        # Check if we should update 
                        if input(f"  Update feature vector for image {image.id}? (y/n): ").lower() == 'y':
                            # Serialize new embedding
                            serialized = suspect_tracking_service._serialize_feature_vector(new_embedding)
                            
                            # Update in database
                            image.feature_vector = serialized
                            db.commit()
                            logger.info(f"  Updated feature vector for image {image.id}")
                    else:
                        logger.error(f"  Failed to regenerate embedding from image")
                        
                except Exception as e:
                    logger.error(f"  Error regenerating embedding: {str(e)}")
        
        # Update suspect tracking service to reload all embeddings
        suspect_tracking_service.load_known_faces()
                
    except Exception as e:
        logger.error(f"Error checking suspects: {str(e)}")
    finally:
        db.close()
        
if __name__ == "__main__":
    # Get suspect ID from command line if provided
    suspect_id = None
    if len(sys.argv) > 1:
        suspect_id = int(sys.argv[1])
        
    check_suspect_embeddings(suspect_id) 