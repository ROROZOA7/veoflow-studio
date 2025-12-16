"""
Render API endpoints
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.scene import Scene
from app.models.project import Project
from app.workers.render_worker import render_scene_task, get_task_status
from pydantic import BaseModel
from typing import List

router = APIRouter()
logger = logging.getLogger(__name__)


class RenderResponse(BaseModel):
    task_id: str
    status: str
    scene_id: str


class RenderAllResponse(BaseModel):
    task_ids: List[str]
    status: str
    scenes_count: int


@router.post("/scenes/{scene_id}/render", response_model=RenderResponse)
async def start_render(
    scene_id: str,
    project_id: str = Query(..., description="Project ID"),
    db: Session = Depends(get_db)
):
    """Start rendering a scene"""
    logger.info(f"Render request received: scene_id={scene_id}, project_id={project_id}")
    
    try:
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            logger.error(f"Scene not found: {scene_id}")
            raise HTTPException(status_code=404, detail="Scene not found")
        
        logger.info(f"Scene found: {scene.id}, status={scene.status}, prompt={scene.prompt[:50]}...")
        
        # Update scene status to pending
        scene.status = "pending"
        db.commit()
        logger.info(f"Scene status updated to 'pending'")
        
        # Queue render task
        logger.info(f"Queuing Celery task for scene {scene_id}")
        task = render_scene_task.delay(scene_id, project_id)
        logger.info(f"Celery task queued: task_id={task.id}")
        
        return {
            "task_id": task.id,
            "status": "queued",
            "scene_id": scene_id
        }
    except Exception as e:
        logger.error(f"Failed to start render: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start render: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_render_status(task_id: str):
    """Get render task status"""
    result = get_task_status(task_id)
    return result


@router.post("/projects/{project_id}/render-all", response_model=RenderAllResponse)
async def render_all_scenes(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Render all pending scenes in a project"""
    logger.info(f"Render all scenes request received for project: {project_id}")
    
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get all pending scenes (exclude completed, rendering, and failed scenes)
        # Note: Deleted scenes are automatically excluded since they don't exist in the database
        all_scenes = db.query(Scene).filter(
            Scene.project_id == project_id
        ).order_by(Scene.number).all()
        
        # Filter to only pending scenes
        scenes = [s for s in all_scenes if s.status == "pending"]
        
        logger.info(f"Total scenes in project: {len(all_scenes)}, Pending scenes: {len(scenes)}")
        
        if not scenes:
            logger.warning(f"No pending scenes found for project {project_id}")
            raise HTTPException(status_code=400, detail="No pending scenes to render")
        
        # Get render settings from project
        render_settings = project.get_render_settings()
        logger.info(f"Using render settings: {render_settings}")
        
        # Queue render tasks for all scenes with delays to avoid browser conflicts
        # IMPORTANT: Each scene needs its own browser instance, so we space them out
        task_ids = []
        for idx, scene in enumerate(scenes):
            # Update scene status to pending (in case it wasn't)
            scene.status = "pending"
            db.commit()
            
            # Queue render task with increasing delays between tasks
            # Start with 10 seconds delay for scene 1 (idx=0), then 15s, 20s, etc.
            # This ensures each browser instance has time to initialize properly
            if idx == 0:
                # First scene: start immediately but with a small delay to ensure DB commit
                countdown = 2  # 2 second delay to ensure DB is committed
                task = render_scene_task.apply_async(args=[scene.id, project_id], countdown=countdown)
            else:
                # Subsequent scenes: longer delays (10s + 10s per scene)
                # This prevents browser conflicts and ensures each scene gets a fresh browser instance
                countdown = 10 + (idx * 10)  # 10s, 20s, 30s, etc.
                task = render_scene_task.apply_async(args=[scene.id, project_id], countdown=countdown)
            
            task_ids.append(task.id)
            logger.info(f"Queued render task {task.id} for scene {scene.id} (Scene {scene.number}) with {countdown}s delay")
        
        return {
            "task_ids": task_ids,
            "status": "queued",
            "scenes_count": len(scenes)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start render all: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start render all: {str(e)}")


@router.post("/scenes/{scene_id}/cancel")
async def cancel_render(scene_id: str, db: Session = Depends(get_db)):
    """Cancel a render (mark scene as cancelled)"""
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    scene.status = "cancelled"
    db.commit()
    
    return {"message": "Render cancelled"}

