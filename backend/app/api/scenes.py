"""
Scenes API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.scene import Scene
import uuid

router = APIRouter()


class SceneCreate(BaseModel):
    project_id: str
    number: int
    prompt: str
    script: Optional[str] = None


class SceneUpdate(BaseModel):
    number: Optional[int] = None
    prompt: Optional[str] = None
    script: Optional[str] = None
    status: Optional[str] = None


class SceneResponse(BaseModel):
    id: str
    project_id: str
    number: int
    prompt: str
    script: Optional[str] = None
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    metadata: Optional[dict] = None
    status: str
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[SceneResponse])
async def list_scenes(
    project_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List scenes, optionally filtered by project"""
    query = db.query(Scene)
    if project_id:
        query = query.filter(Scene.project_id == project_id)
    scenes = query.order_by(Scene.number).all()
    return [s.to_dict() for s in scenes]


@router.post("", response_model=SceneResponse)
async def create_scene(
    scene_data: SceneCreate,
    db: Session = Depends(get_db)
):
    """Create a new scene"""
    scene = Scene(
        id=str(uuid.uuid4()),
        project_id=scene_data.project_id,
        number=scene_data.number,
        prompt=scene_data.prompt,
        script=scene_data.script,
        status="pending"
    )
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return scene.to_dict()


@router.get("/{scene_id}", response_model=SceneResponse)
async def get_scene(scene_id: str, db: Session = Depends(get_db)):
    """Get a scene by ID"""
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene.to_dict()


@router.put("/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: str,
    scene_data: SceneUpdate,
    db: Session = Depends(get_db)
):
    """Update a scene"""
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    if scene_data.number is not None:
        scene.number = scene_data.number
    if scene_data.prompt is not None:
        scene.prompt = scene_data.prompt
    if scene_data.script is not None:
        scene.script = scene_data.script
    if scene_data.status is not None:
        scene.status = scene_data.status
    
    db.commit()
    db.refresh(scene)
    return scene.to_dict()


@router.delete("/{scene_id}")
async def delete_scene(scene_id: str, db: Session = Depends(get_db)):
    """Delete a scene"""
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    db.delete(scene)
    db.commit()
    return {"message": "Scene deleted"}

