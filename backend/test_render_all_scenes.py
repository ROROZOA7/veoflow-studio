#!/usr/bin/env python3
"""
Test script for "Render All Scenes" functionality
This script tests the render_all_scenes API endpoint and monitors execution
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.project import Project
from app.models.scene import Scene
from app.workers.render_worker import render_scene_task, celery_app
from celery.result import AsyncResult

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_test_project(project_id: str = None) -> tuple[Project, list[Scene]]:
    """Find a project with pending scenes for testing"""
    db: Session = SessionLocal()
    try:
        if project_id:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                logger.error(f"Project {project_id} not found")
                return None, []
        else:
            # Find first project with pending scenes
            projects = db.query(Project).all()
            for proj in projects:
                scenes = db.query(Scene).filter(
                    Scene.project_id == proj.id,
                    Scene.status == "pending"
                ).order_by(Scene.number).all()
                if scenes:
                    logger.info(f"Found project: {proj.id} ({proj.name or 'Unnamed'}) with {len(scenes)} pending scenes")
                    return proj, scenes
        
        if project_id:
            scenes = db.query(Scene).filter(
                Scene.project_id == project_id
            ).order_by(Scene.number).all()
            
            # Filter to pending scenes
            pending_scenes = [s for s in scenes if s.status == "pending"]
            if pending_scenes:
                logger.info(f"Found project: {project.id} with {len(pending_scenes)} pending scenes")
                return project, pending_scenes
            else:
                logger.warning(f"Project {project_id} found but no pending scenes. All scenes: {[s.status for s in scenes]}")
                return project, scenes
        
        logger.error("No project with pending scenes found")
        return None, []
    finally:
        db.close()


def render_all_scenes_test(project_id: str):
    """Test render_all_scenes by directly calling Celery tasks"""
    logger.info("=" * 80)
    logger.info("RENDER ALL SCENES TEST")
    logger.info("=" * 80)
    
    project, scenes = find_test_project(project_id)
    
    if not project or not scenes:
        logger.error("Cannot run test: No project or scenes found")
        return False
    
    logger.info(f"\nProject ID: {project.id}")
    logger.info(f"Project Name: {project.name or 'Unnamed'}")
    logger.info(f"Total Scenes: {len(scenes)}")
    logger.info(f"\nScenes to render:")
    for scene in scenes:
        logger.info(f"  - Scene {scene.number}: {scene.id} (status: {scene.status}, prompt: {scene.prompt[:50]}...)")
    
    # Check render settings
    render_settings = project.get_render_settings()
    logger.info(f"\nRender Settings: {render_settings}")
    
    # Queue render tasks similar to render_all_scenes API
    logger.info("\n" + "=" * 80)
    logger.info("QUEUING RENDER TASKS")
    logger.info("=" * 80)
    
    task_ids = []
    for idx, scene in enumerate(scenes):
        # Update scene status to pending (in case it wasn't)
        db = SessionLocal()
        try:
            scene_db = db.query(Scene).filter(Scene.id == scene.id).first()
            if scene_db:
                scene_db.status = "pending"
                db.commit()
                logger.info(f"Scene {scene.number} status set to 'pending'")
        except Exception as e:
            logger.error(f"Failed to update scene {scene.number} status: {e}")
        finally:
            db.close()
        
        # Queue render task with delays (matching API behavior)
        if idx == 0:
            countdown = 2  # First scene: 2 second delay
        else:
            countdown = 10 + (idx * 10)  # Subsequent: 10s, 20s, 30s, etc.
        
        task = render_scene_task.apply_async(args=[scene.id, project.id], countdown=countdown)
        task_ids.append((task.id, scene.id, scene.number, countdown))
        
        logger.info(f"Queued Scene {scene.number}: task_id={task.id}, scene_id={scene.id}, countdown={countdown}s")
    
    logger.info(f"\n✓ All {len(task_ids)} tasks queued successfully")
    
    # Monitor task execution
    logger.info("\n" + "=" * 80)
    logger.info("MONITORING TASK EXECUTION")
    logger.info("=" * 80)
    
    results = {}
    max_wait_time = 600  # 10 minutes max wait
    start_time = time.time()
    check_interval = 5  # Check every 5 seconds
    
    while task_ids:
        elapsed = time.time() - start_time
        if elapsed > max_wait_time:
            logger.warning(f"\nTimeout after {max_wait_time}s. Some tasks may still be running.")
            break
        
        logger.info(f"\n--- Checking tasks (elapsed: {elapsed:.0f}s) ---")
        
        for task_id, scene_id, scene_number, countdown in list(task_ids):
            try:
                result = AsyncResult(task_id, app=celery_app)
                state = result.state
                
                logger.info(f"Scene {scene_number} (task {task_id[:8]}...): {state}")
                
                if state == "SUCCESS":
                    results[scene_number] = {"state": state, "result": result.result}
                    logger.info(f"  ✓ Scene {scene_number} completed successfully")
                    if result.result:
                        logger.info(f"    Result: {result.result}")
                    task_ids.remove((task_id, scene_id, scene_number, countdown))
                elif state == "FAILURE":
                    error = result.info
                    results[scene_number] = {"state": state, "error": str(error)}
                    logger.error(f"  ✗ Scene {scene_number} failed: {error}")
                    task_ids.remove((task_id, scene_id, scene_number, countdown))
                elif state == "PENDING":
                    # Check if task is still waiting for countdown
                    if elapsed < countdown:
                        logger.info(f"  ⏳ Scene {scene_number} waiting (countdown: {countdown}s, elapsed: {elapsed:.0f}s)")
                    else:
                        logger.info(f"  ⏳ Scene {scene_number} should be starting soon...")
                elif state == "STARTED":
                    logger.info(f"  ▶ Scene {scene_number} is currently executing...")
                elif state == "RETRY":
                    logger.warning(f"  ↻ Scene {scene_number} is retrying...")
                    
            except Exception as e:
                logger.error(f"Error checking task {task_id}: {e}")
        
        if task_ids:
            logger.info(f"\nWaiting {check_interval}s before next check...")
            time.sleep(check_interval)
        
        # Also check scene status in database
        db = SessionLocal()
        try:
            for scene in scenes:
                scene_db = db.query(Scene).filter(Scene.id == scene.id).first()
                if scene_db:
                    logger.debug(f"Scene {scene.number} DB status: {scene_db.status}")
        except:
            pass
        finally:
            db.close()
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 80)
    
    # Check final scene statuses in database
    db = SessionLocal()
    try:
        for scene in scenes:
            scene_db = db.query(Scene).filter(Scene.id == scene.id).first()
            if scene_db:
                logger.info(f"Scene {scene.number}: status={scene_db.status}, video_path={scene_db.video_path or 'None'}")
    finally:
        db.close()
    
    success_count = sum(1 for r in results.values() if r.get("state") == "SUCCESS")
    failure_count = sum(1 for r in results.values() if r.get("state") == "FAILURE")
    
    logger.info(f"\nTasks completed: {success_count} success, {failure_count} failures, {len(task_ids)} still running")
    
    if success_count == len(scenes):
        logger.info("\n✓ ALL SCENES RENDERED SUCCESSFULLY!")
        return True
    else:
        logger.warning(f"\n⚠ Some scenes may have failed or are still running")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Render All Scenes functionality")
    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="Specific project ID to test (default: find first project with pending scenes)"
    )
    
    args = parser.parse_args()
    
    try:
        success = render_all_scenes_test(args.project_id)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nTest failed with error: {e}", exc_info=True)
        sys.exit(1)


