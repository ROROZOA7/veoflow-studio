"""
Scenes API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.scene import Scene
from app.models.project import Project
from app.models.script import Script
from app.services.scene_prompt_generator import ScenePromptGenerator
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SceneCreate(BaseModel):
    project_id: str
    number: int
    prompt: str
    script: Optional[str] = None
    scene_description: Optional[str] = None
    duration_sec: Optional[int] = None
    visual_style: Optional[str] = None
    environment: Optional[str] = None
    camera_angle: Optional[str] = None
    character_adaptations: Optional[dict] = None


class SceneUpdate(BaseModel):
    number: Optional[int] = None
    prompt: Optional[str] = None
    script: Optional[str] = None
    scene_description: Optional[str] = None
    duration_sec: Optional[int] = None
    visual_style: Optional[str] = None
    environment: Optional[str] = None
    camera_angle: Optional[str] = None
    character_adaptations: Optional[dict] = None
    status: Optional[str] = None


class SceneGeneratePromptsRequest(BaseModel):
    script_id: str
    character_dna: list
    style: str
    aspect_ratio: str
    target_audience: str


class SceneResponse(BaseModel):
    id: str
    project_id: str
    number: int
    prompt: str
    script: Optional[str] = None
    scene_description: Optional[str] = None
    duration_sec: Optional[int] = None
    visual_style: Optional[str] = None
    environment: Optional[str] = None
    camera_angle: Optional[str] = None
    character_adaptations: Optional[dict] = None
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


@router.post("/projects/{project_id}/generate-prompts")
async def generate_scene_prompts(
    project_id: str,
    request: SceneGeneratePromptsRequest,
    db: Session = Depends(get_db)
):
    """Generate detailed prompts for all scenes"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    script = db.query(Script).filter(Script.id == request.script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    try:
        # Get script scenes (we'll need to reconstruct from script data)
        # For now, get existing scenes or create from script
        existing_scenes = db.query(Scene).filter(
            Scene.project_id == project_id
        ).order_by(Scene.number).all()
        
        if not existing_scenes:
            raise HTTPException(
                status_code=400,
                detail="No scenes found. Generate script first."
            )
        
        # Convert scenes to format expected by generator
        script_scenes = []
        for scene in existing_scenes:
            script_scenes.append({
                "scene_number": scene.number,
                "description": scene.scene_description or scene.prompt[:200],
                "duration_sec": scene.duration_sec or 30,
                "visual_style": scene.visual_style or request.style,
                "environment": scene.environment or "",
                "camera_framing": scene.camera_angle or "medium shot",
                "characters": []  # Will be populated from character_adaptations
            })
        
        # Generate detailed prompts
        scene_prompt_generator = ScenePromptGenerator()
        detailed_scenes = await scene_prompt_generator.generate_scene_prompts(
            script_scenes=script_scenes,
            character_dna_list=request.character_dna,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            target_audience=request.target_audience
        )
        
        # Update existing scenes with detailed prompts
        updated_scenes = []
        for i, scene_data in enumerate(detailed_scenes):
            if i < len(existing_scenes):
                scene = existing_scenes[i]
                scene.prompt = scene_data.get("prompt", scene.prompt)
                scene.scene_description = scene_data.get("scene_description", scene.scene_description)
                scene.duration_sec = scene_data.get("duration_sec", scene.duration_sec)
                scene.visual_style = scene_data.get("visual_style", scene.visual_style)
                scene.environment = scene_data.get("environment", scene.environment)
                scene.camera_angle = scene_data.get("camera_angle", scene.camera_angle)
                scene.character_adaptations = scene_data.get("character_adaptations", {})
            else:
                # Create new scene if more were generated
                scene = Scene(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    number=scene_data.get("scene_number", i + 1),
                    prompt=scene_data.get("prompt", ""),
                    scene_description=scene_data.get("scene_description", ""),
                    duration_sec=scene_data.get("duration_sec", 30),
                    visual_style=scene_data.get("visual_style", ""),
                    environment=scene_data.get("environment", ""),
                    camera_angle=scene_data.get("camera_angle", ""),
                    character_adaptations=scene_data.get("character_adaptations", {}),
                    status="pending"
                )
                db.add(scene)
            
            updated_scenes.append(scene.to_dict())
        
        db.commit()
        
        return {
            "scenes": updated_scenes,
            "total_scenes_created": len(updated_scenes)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate scene prompts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate scene prompts: {str(e)}")


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
        scene_description=scene_data.scene_description,
        duration_sec=scene_data.duration_sec,
        visual_style=scene_data.visual_style,
        environment=scene_data.environment,
        camera_angle=scene_data.camera_angle,
        character_adaptations=scene_data.character_adaptations or {},
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
    
    # Update all fields
    update_data = scene_data.dict(exclude_none=True)
    for key, value in update_data.items():
        if hasattr(scene, key):
            setattr(scene, key, value)
    
    # Validate duration if updating
    if scene_data.duration_sec is not None:
        # Check if sum of durations equals script total duration
        script = db.query(Script).filter(Script.project_id == scene.project_id).first()
        if script:
            all_scenes = db.query(Scene).filter(Scene.project_id == scene.project_id).all()
            total_duration = sum(s.duration_sec or 0 for s in all_scenes)
            # Adjust current scene duration
            total_duration = total_duration - (scene.duration_sec or 0) + scene_data.duration_sec
            if total_duration != script.video_duration:
                logger.warning(
                    f"Scene durations sum to {total_duration}, expected {script.video_duration}"
                )
    
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

