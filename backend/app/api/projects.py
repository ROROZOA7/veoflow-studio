"""
Projects API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.project import Project
from app.models.scene import Scene
from app.services.script_generator import ScriptGenerator
from app.services.scene_builder import SceneBuilder
from app.services.video_processor import VideoProcessor
import uuid
import os
from pathlib import Path

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    script: Optional[str] = None


class ScriptGenerateRequest(BaseModel):
    prompt: str


class StitchRequest(BaseModel):
    transition: str = "fade"
    transition_duration: float = 0.5


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    script: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project"""
    project = Project(
        id=str(uuid.uuid4()),
        name=project_data.name,
        description=project_data.description
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project.to_dict()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    """List all projects"""
    projects = db.query(Project).all()
    return [p.to_dict() for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@router.post("/{project_id}/generate-script")
async def generate_script(
    project_id: str,
    request: ScriptGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate script and scenes from prompt"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Generate script
    script_generator = ScriptGenerator()
    result = await script_generator.generate_script(request.prompt)
    
    # Update project with script
    project.script = result["text"]
    project.project_metadata = result.get("metadata", {})
    db.commit()
    
    # Create scenes
    scene_builder = SceneBuilder()
    optimized_scenes = scene_builder.build_scene_prompts(
        result["scenes"],
        result.get("characters", []),
        result.get("metadata", {}).get("cinematicStyle")
    )
    
    # Delete existing scenes
    db.query(Scene).filter(Scene.project_id == project_id).delete()
    
    # Create new scenes
    created_scenes = []
    for scene_data in optimized_scenes:
        scene = Scene(
            id=str(uuid.uuid4()),
            project_id=project_id,
            number=scene_data["number"],
            prompt=scene_data["prompt"],
            script=scene_data.get("script", ""),
            status="pending"
        )
        db.add(scene)
        created_scenes.append(scene.to_dict())
    
    db.commit()
    
    return {
        "script": result["text"],
        "scenes": created_scenes,
        "characters": result.get("characters", []),
        "metadata": result.get("metadata", {})
    }


@router.post("/{project_id}/stitch")
async def stitch_videos(
    project_id: str,
    request: StitchRequest,
    db: Session = Depends(get_db)
):
    """Stitch all completed scene videos into final video"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all completed scenes
    scenes = db.query(Scene).filter(
        Scene.project_id == project_id,
        Scene.status == "completed"
    ).order_by(Scene.number).all()
    
    if not scenes:
        raise HTTPException(status_code=400, detail="No completed scenes to stitch")
    
    # Get video paths
    scene_paths = [s.video_path for s in scenes if s.video_path and os.path.exists(s.video_path)]
    
    if not scene_paths:
        raise HTTPException(status_code=400, detail="No valid video files found")
    
    # Create output path
    from app.config import DOWNLOADS_PATH
    output_dir = os.path.join(DOWNLOADS_PATH, project_id)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"final_{project_id}.mp4")
    
    # Stitch videos
    processor = VideoProcessor()
    final_path = processor.stitch_scenes(
        scene_paths,
        output_path,
        request.transition,
        request.transition_duration
    )
    
    return {
        "video_path": final_path,
        "scenes_count": len(scene_paths)
    }


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.script is not None:
        project.script = project_data.script
    
    db.commit()
    db.refresh(project)
    return project.to_dict()


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}
