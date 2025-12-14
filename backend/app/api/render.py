"""
Render API endpoints
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.scene import Scene
from app.workers.render_worker import render_scene_task, get_task_status
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class RenderResponse(BaseModel):
    task_id: str
    status: str
    scene_id: str


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


@router.post("/scenes/{scene_id}/cancel")
async def cancel_render(scene_id: str, db: Session = Depends(get_db)):
    """Cancel a render (mark scene as cancelled)"""
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    scene.status = "cancelled"
    db.commit()
    
    return {"message": "Render cancelled"}

