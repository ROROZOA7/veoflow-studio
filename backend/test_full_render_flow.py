#!/usr/bin/env python3
"""
Full render flow test - Tests complete video creation workflow
"""
import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.render_manager import RenderManager
from app.services.profile_manager import ProfileManager
from app.core.database import SessionLocal
from app.models.project import Project
from app.models.scene import Scene
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_full_render_flow():
    """Test the complete render flow from start to finish"""
    try:
        logger.info("=" * 80)
        logger.info("FULL RENDER FLOW TEST")
        logger.info("=" * 80)
        
        # Step 1: Verify profile
        logger.info("\n[STEP 1] Checking active profile...")
        profile_manager = ProfileManager()
        active_profile = profile_manager.get_active_profile()
        
        if not active_profile:
            logger.error("✗ No active profile found!")
            logger.error("Please set an active profile first using the API or UI")
            return False
        
        logger.info(f"✓ Active profile: {active_profile.name} ({active_profile.id})")
        logger.info(f"✓ Profile path: {active_profile.profile_path}")
        
        # Step 2: Create a test project
        logger.info("\n[STEP 2] Creating test project...")
        db = SessionLocal()
        try:
            import uuid
            test_project = Project(
                id=str(uuid.uuid4()),
                name="test-full-render-flow",
                description="Full render flow test"
            )
            db.add(test_project)
            db.commit()
            db.refresh(test_project)
            logger.info(f"✓ Project created: {test_project.id} - {test_project.name}")
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to create project: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            db.close()
        
        # Step 3: Create a simple test scene
        logger.info("\n[STEP 3] Creating test scene...")
        db = SessionLocal()
        try:
            import uuid
            test_scene = Scene(
                id=str(uuid.uuid4()),
                project_id=test_project.id,
                number=1,
                prompt="A beautiful sunset over the ocean with waves gently crashing on the shore",
                status="pending"
            )
            db.add(test_scene)
            db.commit()
            db.refresh(test_scene)
            logger.info(f"✓ Scene created: {test_scene.id} - Scene {test_scene.number}")
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to create scene: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            db.close()
        
        # Step 4: Initialize render manager
        logger.info("\n[STEP 4] Initializing render manager...")
        render_manager = RenderManager()
        logger.info("✓ Render manager initialized")
        
        # Step 5: Render the scene
        logger.info("\n[STEP 5] Rendering scene...")
        logger.info("This may take 2-4 minutes...")
        
        scene_dict = {
            "id": str(test_scene.id),
            "prompt": test_scene.prompt,
            "number": test_scene.number
        }
        
        start_time = time.time()
        try:
            result = await render_manager.render_scene(
                scene=scene_dict,
                project_id=str(test_project.id),
                characters=None
            )
            elapsed_time = time.time() - start_time
            
            if result.get("success"):
                logger.info(f"✓ Scene rendered successfully in {elapsed_time:.1f} seconds")
                logger.info(f"✓ Video path: {result.get('video_path')}")
                
                # Verify video file exists
                video_path = Path(result.get('video_path'))
                if video_path.exists():
                    file_size = video_path.stat().st_size
                    logger.info(f"✓ Video file exists: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
                else:
                    logger.warning(f"⚠ Video file not found at: {video_path}")
                
                logger.info("\n" + "=" * 80)
                logger.info("✓ FULL RENDER FLOW TEST PASSED")
                logger.info("=" * 80)
                return True
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"✗ Scene render failed: {error}")
                logger.error(f"✗ Elapsed time: {elapsed_time:.1f} seconds")
                return False
                
        except Exception as render_error:
            elapsed_time = time.time() - start_time
            logger.error(f"✗ Render exception: {render_error}")
            logger.error(f"✗ Elapsed time: {elapsed_time:.1f} seconds")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            # Cleanup
            try:
                await render_manager.close()
            except:
                pass
        
    except Exception as e:
        logger.error(f"✗ Test failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = asyncio.run(test_full_render_flow())
    sys.exit(0 if success else 1)

