#!/usr/bin/env python3
"""
Test full render flow to verify video generation works end-to-end
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.profile_manager import ProfileManager
from app.services.render_manager import RenderManager
from app.models.project import Project
from app.models.scene import Scene
from app.core.database import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_full_render():
    """Test the full render flow"""
    logger.info("=" * 80)
    logger.info("FULL RENDER FLOW TEST")
    logger.info("=" * 80)
    
    # Check active profile
    logger.info("\n[STEP 1] Checking active profile...")
    profile_manager = ProfileManager()
    active_profile = profile_manager.get_active_profile()
    if not active_profile:
        logger.error("✗ No active profile found. Please set one using the API or setup_chrome_profile.sh")
        return False
    logger.info(f"✓ Active profile: {active_profile.name} ({active_profile.id})")
    logger.info(f"✓ Profile path: {active_profile.profile_path}")
    
    # Create test project and scene
    logger.info("\n[STEP 2] Creating test project and scene...")
    with SessionLocal() as db:
        # Create project
        project = Project(
            name="test-full-render",
            description="Automated test for full render flow"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id
        logger.info(f"✓ Project created: {project_id}")
        
        # Create scene
        scene = Scene(
            project_id=project_id,
            number=1,
            prompt="A beautiful sunset over the ocean with waves gently crashing on the shore, cinematic wide shot, golden hour lighting",
            status="pending"
        )
        db.add(scene)
        db.commit()
        db.refresh(scene)
        scene_id = scene.id
        logger.info(f"✓ Scene created: {scene_id}")
        
        scene_dict = scene.to_dict()
    
    # Initialize render manager
    logger.info("\n[STEP 3] Initializing render manager...")
    render_manager = RenderManager(worker_id="test_worker")
    logger.info("✓ Render manager initialized")
    
    # Render scene
    logger.info("\n[STEP 4] Rendering scene...")
    logger.info("This may take 2-4 minutes...")
    
    try:
        result = await render_manager.render_scene(
            scene=scene_dict,
            project_id=project_id,
            characters=[]
        )
        
        if result.get("success"):
            video_path = result.get("video_path")
            logger.info(f"\n✅ SUCCESS! Video created at: {video_path}")
            
            # Verify file exists
            if Path(video_path).exists():
                file_size = Path(video_path).stat().st_size
                logger.info(f"✓ Video file exists: {file_size:,} bytes")
                return True
            else:
                logger.error(f"✗ Video file not found at: {video_path}")
                return False
        else:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"\n✗ Scene render failed: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"\n✗ An unexpected error occurred during rendering: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await render_manager.close()

if __name__ == "__main__":
    try:
        success = asyncio.run(test_full_render())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

