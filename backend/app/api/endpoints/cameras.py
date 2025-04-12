# backend/app/api/endpoints/cameras.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.camera import Camera as CameraModel
from app.schemas.camera import Camera, CameraCreate, CameraUpdate

router = APIRouter()

@router.get("/", response_model=List[Camera])
def get_cameras(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get all registered cameras
    """
    query = db.query(CameraModel)
    if is_active is not None:
        query = query.filter(CameraModel.is_active == is_active)
    
    return query.all()

@router.post("/", response_model=Camera)
def create_camera(
    camera: CameraCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new camera
    """
    existing_camera = db.query(CameraModel).filter(CameraModel.name == camera.name).first()
    if existing_camera:
        raise HTTPException(status_code=400, detail="Camera name already registered")
    
    db_camera = CameraModel(**camera.model_dump())
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

@router.get("/{camera_id}", response_model=Camera)
def get_camera(
    camera_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific camera by ID
    """
    camera = db.query(CameraModel).filter(CameraModel.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera

@router.put("/{camera_id}", response_model=Camera)
def update_camera(
    camera_id: str,
    camera: CameraUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a camera's information
    """
    db_camera = db.query(CameraModel).filter(CameraModel.camera_id == camera_id).first()
    if not db_camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    for key, value in camera.model_dump(exclude_unset=True).items():
        setattr(db_camera, key, value)
    
    db.commit()
    db.refresh(db_camera)
    return db_camera

@router.delete("/{camera_id}")
def delete_camera(
    camera_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a camera
    """
    camera = db.query(CameraModel).filter(CameraModel.camera_id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    db.delete(camera)
    db.commit()
    return {"message": "Camera deleted successfully"}