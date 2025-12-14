#!/usr/bin/env python3
"""
Test render settings functionality
Tests creating projects with render settings, updating them, and verifying they work
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.project import Project
from app.models.scene import Scene
from app.core.database import SessionLocal, engine, Base
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_render_settings_model():
    """Test Project model render settings methods"""
    logger.info("=" * 80)
    logger.info("TEST 1: Project Model Render Settings")
    logger.info("=" * 80)
    
    # Create project in memory (not saved to DB)
    project = Project(
        name="test-render-settings",
        description="Test project for render settings"
    )
    
    # Test default render settings
    settings = project.get_render_settings()
    logger.info(f"Default settings: {settings}")
    
    assert settings["aspect_ratio"] == "16:9", f"Expected '16:9', got '{settings['aspect_ratio']}'"
    assert settings["videos_per_scene"] == 2, f"Expected 2, got {settings['videos_per_scene']}"
    assert settings["model"] == "veo3.1-fast", f"Expected 'veo3.1-fast', got '{settings['model']}'"
    logger.info("✓ Default render settings are correct")
    
    # Test updating render settings
    project.update_render_settings(
        aspect_ratio="9:16",
        videos_per_scene=3,
        model="veo3.1-standard"
    )
    
    updated_settings = project.get_render_settings()
    logger.info(f"Updated settings: {updated_settings}")
    
    assert updated_settings["aspect_ratio"] == "9:16", f"Expected '9:16', got '{updated_settings['aspect_ratio']}'"
    assert updated_settings["videos_per_scene"] == 3, f"Expected 3, got {updated_settings['videos_per_scene']}"
    assert updated_settings["model"] == "veo3.1-standard", f"Expected 'veo3.1-standard', got '{updated_settings['model']}'"
    logger.info("✓ Render settings update works correctly")
    
    # Test partial update
    project.update_render_settings(aspect_ratio="16:9")
    partial_settings = project.get_render_settings()
    assert partial_settings["aspect_ratio"] == "16:9"
    assert partial_settings["videos_per_scene"] == 3  # Should remain unchanged
    assert partial_settings["model"] == "veo3.1-standard"  # Should remain unchanged
    logger.info("✓ Partial render settings update works correctly")
    
    logger.info("✓ TEST 1 PASSED: Project model render settings work correctly\n")
    return True


def test_render_settings_database():
    """Test render settings persistence in database"""
    logger.info("=" * 80)
    logger.info("TEST 2: Render Settings Database Persistence")
    logger.info("=" * 80)
    
    with SessionLocal() as db:
        # Create project with default settings
        project = Project(
            name="test-db-settings",
            description="Test database persistence"
        )
        # Initialize default settings
        project.update_render_settings(
            aspect_ratio="16:9",
            videos_per_scene=2,
            model="veo3.1-fast"
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        project_id = project.id
        logger.info(f"Created project ID: {project_id}")
        
        # Retrieve and verify settings
        settings = project.get_render_settings()
        logger.info(f"Initial settings: {settings}")
        assert settings["aspect_ratio"] == "16:9"
        assert settings["videos_per_scene"] == 2
        assert settings["model"] == "veo3.1-fast"
        logger.info("✓ Initial settings saved correctly")
        
        # Update settings
        project.update_render_settings(
            aspect_ratio="9:16",
            videos_per_scene=4,
            model="veo3.1-standard"
        )
        db.commit()
        db.refresh(project)
        
        # Verify updated settings
        updated_settings = project.get_render_settings()
        logger.info(f"Updated settings: {updated_settings}")
        assert updated_settings["aspect_ratio"] == "9:16"
        assert updated_settings["videos_per_scene"] == 4
        assert updated_settings["model"] == "veo3.1-standard"
        logger.info("✓ Updated settings saved correctly")
        
        # Query fresh from database
        fresh_project = db.query(Project).filter(Project.id == project_id).first()
        fresh_settings = fresh_project.get_render_settings()
        logger.info(f"Fresh query settings: {fresh_settings}")
        assert fresh_settings["aspect_ratio"] == "9:16"
        assert fresh_settings["videos_per_scene"] == 4
        assert fresh_settings["model"] == "veo3.1-standard"
        logger.info("✓ Settings persist correctly across queries")
        
        # Test to_dict includes render_settings
        project_dict = project.to_dict()
        assert "render_settings" in project_dict, "to_dict() should include render_settings"
        assert project_dict["render_settings"]["aspect_ratio"] == "9:16"
        logger.info("✓ to_dict() includes render_settings correctly")
        
        # Cleanup
        db.delete(project)
        db.commit()
        logger.info("✓ Cleaned up test project")
    
    logger.info("✓ TEST 2 PASSED: Render settings database persistence works correctly\n")
    return True


def test_project_with_scenes():
    """Test project with 2 scenes and render settings"""
    logger.info("=" * 80)
    logger.info("TEST 3: Project with 2 Scenes and Render Settings")
    logger.info("=" * 80)
    
    with SessionLocal() as db:
        # Create project with custom render settings
        project = Project(
            name="test-2-scenes",
            description="Test project with 2 scenes"
        )
        project.update_render_settings(
            aspect_ratio="9:16",
            videos_per_scene=2,
            model="veo3.1-fast"
        )
        
        db.add(project)
        db.flush()  # Flush to get project.id
        
        project_id = project.id
        logger.info(f"Created project ID: {project_id}")
        logger.info(f"Project render settings: {project.get_render_settings()}")
        
        # Create 2 scenes
        scene1 = Scene(
            project_id=project_id,
            number=1,
            prompt="A red dragon flying through clouds",
            status="pending"
        )
        
        scene2 = Scene(
            project_id=project_id,
            number=2,
            prompt="The dragon destroying a monster",
            status="pending"
        )
        
        db.add(scene1)
        db.add(scene2)
        db.commit()
        db.refresh(project)
        db.refresh(scene1)
        db.refresh(scene2)
        
        logger.info(f"Created scene 1: {scene1.id} - {scene1.prompt}")
        logger.info(f"Created scene 2: {scene2.id} - {scene2.prompt}")
        
        # Verify project settings are accessible
        settings = project.get_render_settings()
        logger.info(f"Project settings for rendering: {settings}")
        
        assert settings["aspect_ratio"] == "9:16"
        assert settings["videos_per_scene"] == 2
        assert settings["model"] == "veo3.1-fast"
        
        # Verify we can get all scenes for this project
        scenes = db.query(Scene).filter(Scene.project_id == project_id).order_by(Scene.number).all()
        assert len(scenes) == 2, f"Expected 2 scenes, got {len(scenes)}"
        logger.info(f"✓ Project has {len(scenes)} scenes")
        
        # Simulate what render_worker would do
        logger.info("\nSimulating render worker flow:")
        logger.info(f"1. Get project: {project.name} (ID: {project_id})")
        logger.info(f"2. Get render settings: {settings}")
        logger.info(f"3. Get scenes: {len(scenes)} scenes")
        logger.info(f"4. Render each scene with settings: aspect={settings['aspect_ratio']}, videos={settings['videos_per_scene']}, model={settings['model']}")
        
        # Cleanup
        db.delete(scene1)
        db.delete(scene2)
        db.delete(project)
        db.commit()
        logger.info("✓ Cleaned up test project and scenes")
    
    logger.info("✓ TEST 3 PASSED: Project with scenes and render settings works correctly\n")
    return True


def test_api_models():
    """Test API request/response models"""
    logger.info("=" * 80)
    logger.info("TEST 4: API Models")
    logger.info("=" * 80)
    
    try:
        from app.api.projects import RenderSettings, ProjectUpdate, ProjectResponse
        
        # Test RenderSettings model
        settings = RenderSettings(
            aspect_ratio="16:9",
            videos_per_scene=2,
            model="veo3.1-fast"
        )
        assert settings.aspect_ratio == "16:9"
        assert settings.videos_per_scene == 2
        assert settings.model == "veo3.1-fast"
        logger.info("✓ RenderSettings model works correctly")
        
        # Test partial RenderSettings (all optional)
        partial_settings = RenderSettings(aspect_ratio="9:16")
        assert partial_settings.aspect_ratio == "9:16"
        assert partial_settings.videos_per_scene is None
        assert partial_settings.model is None
        logger.info("✓ Partial RenderSettings model works correctly")
        
        # Test ProjectUpdate with render_settings
        update = ProjectUpdate(
            name="Updated Name",
            render_settings=RenderSettings(
                aspect_ratio="9:16",
                videos_per_scene=3,
                model="veo3.1-standard"
            )
        )
        assert update.name == "Updated Name"
        assert update.render_settings is not None
        assert update.render_settings.aspect_ratio == "9:16"
        logger.info("✓ ProjectUpdate with render_settings works correctly")
        
        logger.info("✓ TEST 4 PASSED: API models work correctly\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST 4 FAILED: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("=" * 80)
    logger.info("RENDER SETTINGS FUNCTIONALITY TEST SUITE")
    logger.info("=" * 80)
    logger.info("")
    
    tests = [
        ("Model Methods", test_render_settings_model),
        ("Database Persistence", test_render_settings_database),
        ("Project with Scenes", test_project_with_scenes),
        ("API Models", test_api_models),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                logger.error(f"✗ {test_name} failed")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {test_name} failed with exception: {e}", exc_info=True)
    
    logger.info("=" * 80)
    logger.info("TEST RESULTS")
    logger.info("=" * 80)
    logger.info(f"Total tests: {len(tests)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info("=" * 80)
    
    if failed == 0:
        logger.info("✓ ALL TESTS PASSED!")
        return 0
    else:
        logger.error("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())

