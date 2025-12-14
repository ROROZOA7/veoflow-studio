"""
Celery Worker for Render Tasks
"""

import os
import logging
from celery import Celery
from app.config import settings
from app.services.render_manager import RenderManager
from app.models.scene import Scene
from app.models.character import CharacterDNA
from app.models.project import Project
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "veoflow",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # FIX: Increased timeouts for video rendering (can take 2-4 minutes per scene)
    task_time_limit=600,  # 10 minutes (hard limit)
    task_soft_time_limit=540,  # 9 minutes (soft limit - raises SoftTimeLimitExceeded)
)


@celery_app.task(bind=True, max_retries=3)
def render_scene_task(self, scene_id: str, project_id: str):
    """
    Celery task to render a scene
    
    Args:
        scene_id: Scene ID to render
        project_id: Project ID
    
    Returns:
        Render result dictionary
    """
    logger.info(f"=== RENDER TASK STARTED ===")
    logger.info(f"Task ID: {self.request.id}")
    logger.info(f"Scene ID: {scene_id}")
    logger.info(f"Project ID: {project_id}")
    
    db = SessionLocal()
    render_manager = None
    
    try:
        # Get scene from database
        logger.info(f"Fetching scene from database: {scene_id}")
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            logger.error(f"Scene not found in database: {scene_id}")
            raise ValueError(f"Scene {scene_id} not found")
        
        logger.info(f"Scene found: prompt={scene.prompt[:50]}..., status={scene.status}")
        
        # Get project to retrieve render settings
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project not found: {project_id}")
            raise ValueError(f"Project {project_id} not found")
        
        # Get render settings from project
        render_settings = project.get_render_settings()
        logger.info(f"Using render settings: {render_settings}")
        
        # Get characters for this project
        logger.info(f"Fetching characters for project: {project_id}")
        characters = db.query(CharacterDNA).filter(
            CharacterDNA.project_id == project_id
        ).all()
        logger.info(f"Found {len(characters)} characters")
        
        # Convert to dictionaries
        scene_dict = scene.to_dict()
        characters_list = [char.to_dict() for char in characters]
        
        # Update scene status
        logger.info("Updating scene status to 'rendering'")
        scene.status = "rendering"
        db.commit()
        logger.info("Scene status updated")
        
        # Create render manager and render
        # Get worker ID for unique browser profile
        # Celery provides worker name via self.request.hostname
        worker_name = getattr(self.request, 'hostname', None) or os.getenv("CELERY_WORKER_NAME", f"worker_{os.getpid()}")
        worker_id = worker_name.split('@')[0] if '@' in worker_name else worker_name
        logger.info(f"Creating RenderManager with worker_id: {worker_id}")
        render_manager = RenderManager(worker_id=worker_id)
        logger.info("RenderManager created")
        
        # Note: Celery tasks are synchronous, but render_manager uses async
        # We need to run async code in sync context
        import asyncio
        
        # Get or create event loop for this task
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            # Run async render with render settings
            logger.info("Starting async render process...")
            result = loop.run_until_complete(
                render_manager.render_scene(scene_dict, project_id, characters_list, render_settings)
            )
            logger.info(f"Render completed: success={result.get('success')}, error={result.get('error', 'None')}")
        finally:
            # Cleanup render manager
            logger.info("Cleaning up render manager...")
            try:
                loop.run_until_complete(render_manager.close())
                logger.info("Render manager closed")
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")
            # Don't close the loop - it might be reused by Celery
        
        # Update scene status
        # IMPORTANT: Re-query scene to ensure it's attached to the current session
        # After async operations, the scene object might be detached
        logger.info(f"Re-querying scene from database to update status...")
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            logger.error(f"Scene not found when trying to update status: {scene_id}")
            raise ValueError(f"Scene {scene_id} not found when updating status")
        
        logger.info(f"Updating scene status: success={result.get('success')}")
        if result["success"]:
            scene.status = "completed"
            scene.video_path = result.get("video_path")
            logger.info(f"Scene marked as completed. Video path: {scene.video_path}")
        else:
            scene.status = "failed"
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Scene marked as failed. Error: {error_msg}")
        
        db.commit()
        logger.info(f"Scene status updated to '{scene.status}' and committed to database")
        logger.info("=== RENDER TASK COMPLETED ===")
        
        return result
        
    except Exception as exc:
        logger.error(f"Render task failed: {exc}", exc_info=True)
        
        # Update scene status
        try:
            scene = db.query(Scene).filter(Scene.id == scene_id).first()
            if scene:
                scene.status = "failed"
                db.commit()
        except:
            pass
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    
    finally:
        db.close()


@celery_app.task
def get_task_status(task_id: str):
    """Get status of a Celery task"""
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.state,
        "result": task.result if task.ready() else None,
        "info": task.info if hasattr(task, 'info') else None
    }

