from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import os
import shutil
import logging
import json
import numpy as np
from app.core.database import get_db
from app.models.suspect import Suspect, SuspectImage, Case, SuspectLocation
from app.models.alert import Alert as AlertModel
from app.services.suspect_tracking import suspect_tracking_service, reload_suspect_service
from pydantic import BaseModel
from app.core.config import settings
from fastapi.responses import FileResponse

router = APIRouter()
logger = logging.getLogger(__name__)

class SuspectBase(BaseModel):
    name: str
    aliases: Optional[List[str]] = None
    physical_description: Optional[str] = None
    biometric_markers: Optional[dict] = None
    priority_level: int = 1
    is_active: bool = True

class SuspectCreate(SuspectBase):
    pass

class SuspectUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[List[str]] = None
    physical_description: Optional[str] = None
    biometric_markers: Optional[dict] = None
    priority_level: Optional[int] = None
    is_active: Optional[bool] = None

class SuspectImageResponse(BaseModel):
    id: int
    image_path: str
    thumbnail_path: Optional[str] = None
    capture_date: Optional[datetime] = None
    is_primary: bool = False
    has_face_vector: bool = False

class SuspectResponse(SuspectBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    images: List[SuspectImageResponse] = []

class CaseBase(BaseModel):
    case_number: str
    title: str
    description: Optional[str] = None
    status: str
    priority: int

class CaseCreate(CaseBase):
    pass

class CaseResponse(CaseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    suspects: List[dict]

    class Config:
        orm_mode = True

# Define response model for location including snapshot path
class LocationResponse(BaseModel):
    id: int
    suspect_id: int
    camera_id: str
    timestamp: datetime
    confidence: Optional[float] = None
    coordinates: Optional[dict] = None
    snapshot_path: Optional[str] = None

    class Config:
        orm_mode = True

@router.post("/", response_model=SuspectResponse)
def create_suspect(suspect: SuspectCreate, db: Session = Depends(get_db)):
    """Create a new suspect"""
    logger.info(f"Creating new suspect: {suspect.name}")
    db_suspect = Suspect(
        name=suspect.name,
        aliases=suspect.aliases,
        physical_description=suspect.physical_description,
        biometric_markers=suspect.biometric_markers,
        priority_level=suspect.priority_level,
        is_active=suspect.is_active
    )
    db.add(db_suspect)
    db.commit()
    db.refresh(db_suspect)
    logger.info(f"Created suspect with ID: {db_suspect.id}")
    return db_suspect

@router.get("/", response_model=List[SuspectResponse])
def get_suspects(
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all suspects"""
    query = db.query(Suspect)
    if active_only:
        query = query.filter(Suspect.is_active == True)
    return query.offset(skip).limit(limit).all()

@router.get("/{suspect_id}", response_model=SuspectResponse)
def get_suspect(suspect_id: int, db: Session = Depends(get_db)):
    """Get a specific suspect by ID"""
    suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
    if not suspect:
        raise HTTPException(status_code=404, detail="Suspect not found")
    return suspect

@router.put("/{suspect_id}", response_model=SuspectResponse)
def update_suspect(
    suspect_id: int, 
    suspect_update: SuspectUpdate, 
    db: Session = Depends(get_db)
):
    """Update a suspect"""
    db_suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
    if not db_suspect:
        raise HTTPException(status_code=404, detail="Suspect not found")
    
    # Update fields if provided
    update_data = suspect_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_suspect, key, value)
    
    db.commit()
    db.refresh(db_suspect)
    return db_suspect

@router.delete("/{suspect_id}")
def delete_suspect(suspect_id: int, db: Session = Depends(get_db)):
    """Delete a suspect"""
    db_suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
    if not db_suspect:
        raise HTTPException(status_code=404, detail="Suspect not found")
    
    db.delete(db_suspect)
    db.commit()
    return {"message": "Suspect deleted"}

@router.post("/{suspect_id}/images")
async def upload_suspect_image(
    suspect_id: int,
    image: UploadFile = File(...),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Upload an image for a suspect"""
    # Verify suspect exists
    suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
    if not suspect:
        raise HTTPException(status_code=404, detail="Suspect not found")
    
    try:
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join("data", "suspects", str(suspect_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Get absolute path
        abs_upload_dir = os.path.abspath(upload_dir)
        logger.info(f"Saving suspect image to directory: {abs_upload_dir}")
        
        # Save the uploaded file with a timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{image.filename}"
        file_path = os.path.join(abs_upload_dir, filename)
        
        logger.info(f"Saving uploaded file to: {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        logger.info(f"File saved, now processing for face recognition")
        
        # Process the image - add detailed exception handling
        try:
            # First try to detect faces in the image
            face_encoding = suspect_tracking_service.process_image(file_path)
            if face_encoding is None:
                logger.error(f"No faces detected in uploaded image: {file_path}")
                os.remove(file_path)
                raise HTTPException(status_code=400, 
                                   detail="No faces detected in the uploaded image. Please upload an image with a clear face.")
            
            logger.info(f"Face detected and encoded successfully")
            
            # Create thumbnail
            thumbnail_path = suspect_tracking_service._create_thumbnail(file_path)
            logger.info(f"Thumbnail created at: {thumbnail_path}")
            
            # Validate face encoding is a numpy array with correct dimensions
            if not isinstance(face_encoding, np.ndarray):
                logger.error(f"Face encoding is not a numpy array: {type(face_encoding)}")
                os.remove(file_path)
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                raise HTTPException(status_code=400, detail="Invalid face encoding format")
                
            if len(face_encoding) != 128:
                logger.error(f"Face encoding has incorrect dimensions: {len(face_encoding)}")
                os.remove(file_path)
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                raise HTTPException(status_code=400, detail="Invalid face encoding dimensions")
            
            # Convert to JSON string
            feature_vector = json.dumps(face_encoding.tolist())
            logger.info(f"Generated JSON feature vector of length {len(feature_vector)}")
            
            # Verify JSON string is valid
            try:
                parsed = json.loads(feature_vector)
                if not isinstance(parsed, list) or len(parsed) != 128:
                    raise ValueError("Invalid feature vector structure")
                logger.info(f"Successfully validated feature vector JSON with {len(parsed)} elements")
            except Exception as e:
                logger.error(f"Invalid feature vector JSON: {str(e)}")
                os.remove(file_path)
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                raise HTTPException(status_code=400, detail="Failed to create valid feature vector")
            
            # Create the database record
            image_record = SuspectImage(
                suspect_id=suspect_id,
                image_path=file_path,
                thumbnail_path=thumbnail_path,
                feature_vector=feature_vector,  # Guaranteed to be a valid JSON string
                confidence_score=1.0,
                capture_date=datetime.now(),
                source="upload",
                is_primary=is_primary
            )
            
            # If this is primary, update other images
            if is_primary:
                existing_primary = db.query(SuspectImage).filter(
                    SuspectImage.suspect_id == suspect_id,
                    SuspectImage.is_primary == True
                ).all()
                
                for img in existing_primary:
                    img.is_primary = False
            
            # Add and commit the new image
            db.add(image_record)
            db.commit()
            
            # Log the stored feature vector from the DB to verify it's saved correctly
            db_image = db.query(SuspectImage).filter(SuspectImage.id == image_record.id).first()
            logger.info(f"Stored feature vector in DB: type={type(db_image.feature_vector)}, "
                       f"preview={str(db_image.feature_vector)[:100]}")
            
            # Update the tracking service
            logger.info("Reloading suspect tracking service to include new image")
            suspect_tracking_service.load_known_faces()
            
            return {
                "message": "Image uploaded and processed successfully",
                "image_id": image_record.id,
                "has_face_vector": True,
                "is_primary": is_primary
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            # Clean up file if processing failed
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            raise HTTPException(status_code=400, 
                               detail=f"Failed to process image: {str(e)}")
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in upload_suspect_image: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{suspect_id}/images", response_model=List[SuspectImageResponse])
def get_suspect_images(suspect_id: int, db: Session = Depends(get_db)):
    """Get all images for a suspect"""
    suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
    if not suspect:
        raise HTTPException(status_code=404, detail="Suspect not found")
    
    images = db.query(SuspectImage).filter(SuspectImage.suspect_id == suspect_id).all()
    
    # Add has_face_vector field
    for image in images:
        image.has_face_vector = bool(image.feature_vector)
    
    return images

@router.get("/image/{image_id}", response_class=FileResponse)
async def get_suspect_image_file(
    image_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific suspect image file by its ID."""
    image_record = db.query(SuspectImage).filter(SuspectImage.id == image_id).first()
    
    if not image_record or not image_record.image_path:
        raise HTTPException(status_code=404, detail="Image record not found or path is missing")
        
    # Construct the full path (assuming relative or absolute path stored)
    file_path = image_record.image_path 
    if not os.path.isabs(file_path):
        # Assuming it's relative to the base directory or a specific data dir
        # This might need adjustment based on how paths are stored
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # Get project base
        potential_path = os.path.join(base_dir, file_path)
        if os.path.exists(potential_path):
            file_path = potential_path
        else:
            # Fallback: try relative to script location (less ideal)
             file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        logger.error(f"Suspect image file not found at path: {file_path} (Image ID: {image_id})")
        raise HTTPException(status_code=404, detail=f"Image file not found at path: {file_path}")
        
    return FileResponse(file_path, media_type="image/jpeg") # Adjust media_type if needed

@router.delete("/{suspect_id}/images/{image_id}")
def delete_suspect_image(suspect_id: int, image_id: int, db: Session = Depends(get_db)):
    """Delete a suspect image"""
    image = db.query(SuspectImage).filter(
        SuspectImage.id == image_id,
        SuspectImage.suspect_id == suspect_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Try to delete the actual file
    try:
        if image.image_path and os.path.exists(image.image_path):
            os.remove(image.image_path)
        if image.thumbnail_path and os.path.exists(image.thumbnail_path):
            os.remove(image.thumbnail_path)
    except Exception as e:
        logger.warning(f"Error deleting image files: {str(e)}")
    
    # Delete the database record
    db.delete(image)
    db.commit()
    
    # Reload suspect tracking service
    suspect_tracking_service.load_known_faces()
    
    return {"message": "Image deleted"}

@router.get("/{suspect_id}/locations", response_model=List[LocationResponse])
async def get_suspect_locations(
    suspect_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get recent locations for a suspect, including alert snapshot paths"""
    query = db.query(SuspectLocation).filter(SuspectLocation.suspect_id == suspect_id)
    
    if start_time:
        query = query.filter(SuspectLocation.timestamp >= start_time)
    if end_time:
        query = query.filter(SuspectLocation.timestamp <= end_time)
        
    # Get recent locations, ordered by timestamp descending
    locations = query.order_by(SuspectLocation.timestamp.desc()).limit(limit).all()
    
    # Prepare response data
    response_data = []
    for loc in locations:
        # Find corresponding alert snapshot
        time_window = timedelta(seconds=2) # +/- 2 seconds window
        corresponding_alert = db.query(AlertModel).filter(
            AlertModel.suspect_id == loc.suspect_id,
            AlertModel.alert_type == "suspect_detected",
            AlertModel.timestamp >= loc.timestamp - time_window,
            AlertModel.timestamp <= loc.timestamp + time_window
        ).order_by(
            # Order by proximity to location timestamp
            func.abs(func.extract('epoch', AlertModel.timestamp) - func.extract('epoch', loc.timestamp))
        ).first()
        
        # Add snapshot path if found
        snapshot_api_url = None
        if corresponding_alert:
            # Construct the URL to the snapshot API endpoint
            snapshot_api_url = f"{settings.NEXT_PUBLIC_API_URL}/api/alerts/snapshot/{corresponding_alert.id}"
        
        # Append to response, converting to dict first if needed or use the model directly
        response_data.append(LocationResponse(
            id=loc.id,
            suspect_id=loc.suspect_id,
            camera_id=loc.camera_id,
            timestamp=loc.timestamp,
            confidence=loc.confidence,
            coordinates=loc.coordinates,
            snapshot_path=snapshot_api_url
        ))
        
    return response_data

@router.post("/cases/", response_model=CaseResponse)
async def create_case(
    case: CaseCreate,
    db: Session = Depends(get_db)
):
    """Create a new case"""
    try:
        db_case = Case(**case.dict())
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        return db_case
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cases/{case_id}/suspects/{suspect_id}")
async def add_suspect_to_case(
    case_id: int,
    suspect_id: int,
    db: Session = Depends(get_db)
):
    """Add a suspect to a case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    suspect = db.query(Suspect).filter(Suspect.id == suspect_id).first()
    
    if not case or not suspect:
        raise HTTPException(status_code=404, detail="Case or suspect not found")
    
    if suspect not in case.suspects:
        case.suspects.append(suspect)
        db.commit()
    
    return {"message": "Suspect added to case successfully"}

@router.post("/reload_suspect_service")
async def reload_suspect_service_endpoint(
    db: Session = Depends(get_db)
):
    """Reload the suspect tracking service"""
    try:
        status = reload_suspect_service()
        return {
            "message": "Suspect tracking service reloaded successfully",
            "status": status
        }
    except Exception as e:
        logger.error(f"Error reloading suspect service: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/service_status")
async def get_service_status():
    """Get the status of the suspect tracking service"""
    # Count suspects and encodings
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
    
    return status 