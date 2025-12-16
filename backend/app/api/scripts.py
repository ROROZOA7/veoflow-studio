"""
Scripts API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.script import Script
from app.models.project import Project
import uuid

router = APIRouter()


class ScriptResponse(BaseModel):
    id: str
    project_id: str
    main_content: str
    video_duration: int
    style: str
    target_audience: str
    aspect_ratio: str
    language: Optional[str] = None
    voice_style: Optional[str] = None
    music_style: Optional[str] = None
    color_palette: Optional[str] = None
    transition_style: Optional[str] = None
    full_script: Optional[str] = None
    story_structure: Optional[dict] = None
    scene_count: Optional[int] = None
    generated_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class ScriptUpdate(BaseModel):
    main_content: Optional[str] = None
    full_script: Optional[str] = None
    story_structure: Optional[dict] = None


@router.get("/projects/{project_id}/script", response_model=ScriptResponse)
async def get_script(project_id: str, db: Session = Depends(get_db)):
    """Get script for a project"""
    script = db.query(Script).filter(Script.project_id == project_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script.to_dict()


@router.put("/projects/{project_id}/script", response_model=ScriptResponse)
async def update_script(
    project_id: str,
    script_data: ScriptUpdate,
    db: Session = Depends(get_db)
):
    """Update script for a project"""
    script = db.query(Script).filter(Script.project_id == project_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    if script_data.main_content is not None:
        script.main_content = script_data.main_content
    if script_data.full_script is not None:
        script.full_script = script_data.full_script
    if script_data.story_structure is not None:
        script.story_structure = script_data.story_structure
    
    db.commit()
    db.refresh(script)
    return script.to_dict()


@router.delete("/projects/{project_id}/script")
async def delete_script(project_id: str, db: Session = Depends(get_db)):
    """Delete script for a project"""
    script = db.query(Script).filter(Script.project_id == project_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    db.delete(script)
    db.commit()
    return {"message": "Script deleted"}



