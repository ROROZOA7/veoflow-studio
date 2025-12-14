#!/usr/bin/env python3
"""
Standalone test script for full automated video generation
Tests the complete flow: profile → browser → navigate → inject → generate → download
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, init_db
from app.core.logging_config import setup_logging
from app.models.project import Project
from app.models.scene import Scene
from app.models.profile import Profile
from app.services.profile_manager import ProfileManager
from app.services.render_manager import RenderManager
import logging

# Setup logging
setup_logging("INFO")
logger = logging.getLogger(__name__)


async def test_full_automation():
    """Test complete automated video generation flow"""
    
    print("=" * 70)
    print("FULL AUTOMATED VIDEO GENERATION TEST")
    print("=" * 70)
    print()
    
    db = SessionLocal()
    render_manager = None
    
    try:
        # Step 1: Initialize database
        print("1. Initializing database...")
        init_db()
        print("   ✓ Database initialized")
        print()
        
        # Step 2: Create or get active profile
        print("2. Setting up Chrome profile...")
        profile_manager = ProfileManager()
        active_profile = profile_manager.get_active_profile()
        
        if not active_profile:
            print("   No active profile found. Creating default profile...")
            try:
                active_profile = profile_manager.create_profile("test-profile")
                profile_manager.set_active_profile(active_profile.id)
                print(f"   ✓ Created and activated profile: {active_profile.name}")
            except ValueError as e:
                # Profile might already exist
                existing = db.query(Profile).filter(Profile.name == "test-profile").first()
                if existing:
                    profile_manager.set_active_profile(existing.id)
                    active_profile = existing
                    print(f"   ✓ Using existing profile: {active_profile.name}")
                else:
                    raise
        else:
            print(f"   ✓ Using active profile: {active_profile.name}")
        
        profile_path = Path(active_profile.profile_path)
        if not profile_path.exists():
            profile_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✓ Created profile directory: {profile_path}")
        print()
        
        # Step 3: Create test project
        print("3. Creating test project...")
        project_id = "test-auto-001"
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            project = Project(
                id=project_id,
                name="Automated Test Project",
                description="Testing full automation flow"
            )
            db.add(project)
            db.commit()
            print(f"   ✓ Created project: {project.name}")
        else:
            print(f"   ✓ Using existing project: {project.name}")
        print()
        
        # Step 4: Create test scene
        print("4. Creating test scene...")
        scene_id = f"{project_id}-scene-1"
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        
        if not scene:
            scene = Scene(
                id=scene_id,
                project_id=project_id,
                number=1,
                prompt="A person walking through a beautiful city at sunset, wide cinematic shot, golden hour lighting",
                script="Test scene for automation",
                status="pending"
            )
            db.add(scene)
            db.commit()
            print(f"   ✓ Created scene: Scene {scene.number}")
        else:
            print(f"   ✓ Using existing scene: Scene {scene.number}")
        print(f"   Prompt: {scene.prompt[:60]}...")
        print()
        
        # Step 5: Check if profile is logged in
        print("5. Checking login status...")
        render_manager = RenderManager(worker_id="test-automation")
        
        # Initialize browser to check login
        await render_manager.browser_manager.initialize()
        test_page = await render_manager.browser_manager.new_page()
        
        try:
            # Navigate to Flow to check login
            flow_url = "https://labs.google/fx/tools/flow/"
            await test_page.goto(flow_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)  # Wait for page to load
            
            # Check login status
            from app.services.cookie_extractor import CookieExtractor
            cookie_extractor = CookieExtractor(render_manager.browser_manager)
            is_logged_in = await cookie_extractor.verify_login_status(test_page)
            
            current_url = test_page.url
            page_title = await test_page.title()
            
            await test_page.close()
            await render_manager.browser_manager.close()
            
            if not is_logged_in:
                print("   ✗ Profile is NOT logged in to Google Flow")
                print(f"   Current URL: {current_url}")
                print(f"   Page title: {page_title}")
                print()
                print("   ⚠ CANNOT PROCEED - Login required")
                print()
                print("   To fix this:")
                print("   1. Go to the UI: http://localhost:3000/settings")
                print("   2. Create a profile (if needed)")
                print("   3. Click 'Open' on the profile")
                print("   4. Follow the guided login steps:")
                print("      - Login to Gmail")
                print("      - Login to Google Flow")
                print("      - Click 'Confirm Login & Save Cookie'")
                print("   5. Then run this test again")
                print()
                print("=" * 70)
                print("✗ TEST SKIPPED - Profile not logged in")
                print("=" * 70)
                return False
            
            print("   ✓ Profile is logged in to Google Flow")
            print()
        except Exception as e:
            await test_page.close()
            await render_manager.browser_manager.close()
            print(f"   ✗ Error checking login status: {e}")
            print()
            print("   ⚠ CANNOT PROCEED - Could not verify login")
            print("   Please ensure you're logged in via the UI first")
            return False
        
        # Step 6: Run automated render
        print("6. Starting AUTOMATED video generation...")
        print("   This will:")
        print("   - Open browser with your logged-in profile")
        print("   - Navigate to Google Flow")
        print("   - Inject prompt automatically")
        print("   - Click Generate automatically")
        print("   - Wait for video to complete")
        print("   - Download video automatically")
        print()
        print("   Browser window will open - DO NOT CLOSE IT")
        print("   The automation will handle everything")
        print()
        
        scene_dict = {
            "id": scene.id,
            "prompt": scene.prompt,
            "number": scene.number
        }
        
        print("   Starting render (this takes 2-4 minutes)...")
        print()
        
        result = await render_manager.render_scene(
            scene_dict,
            project_id,
            characters=None
        )
        
        print()
        print("7. Render Result:")
        print("   " + "=" * 60)
        
        if result.get("success"):
            print("   ✓ SUCCESS!")
            print(f"   Video path: {result.get('video_path')}")
            print(f"   Scene ID: {result.get('scene_id')}")
            
            # Update scene in database
            scene.status = "completed"
            scene.video_path = result.get("video_path")
            db.commit()
            print()
            print("   ✓ Scene updated in database")
            
            # Verify file exists
            video_path = Path(result.get("video_path"))
            if video_path.exists():
                size_mb = video_path.stat().st_size / (1024 * 1024)
                print(f"   ✓ Video file exists: {size_mb:.2f} MB")
            else:
                print(f"   ⚠ Video file not found at: {video_path}")
        else:
            print("   ✗ FAILED")
            error = result.get("error", "Unknown error")
            print(f"   Error: {error}")
            
            scene.status = "failed"
            db.commit()
            
            if result.get("requires_login"):
                print()
                print("   ⚠ LOGIN REQUIRED")
                print("   Please:")
                print("   1. Go to Settings in the UI")
                print("   2. Create a profile and log in to Google Flow")
                print("   3. Then run this test again")
        
        print("   " + "=" * 60)
        print()
        
        # Final summary
        print("=" * 70)
        if result.get("success"):
            print("✓ TEST PASSED - Video generated successfully!")
        else:
            print("✗ TEST FAILED - Check error message above")
        print("=" * 70)
        
        return result.get("success", False)
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        print()
        print("=" * 70)
        print("✗ TEST FAILED WITH EXCEPTION")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        print("Full traceback:")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()
        if render_manager:
            try:
                await render_manager.close()
                print("   ✓ Browser closed")
            except Exception as e:
                print(f"   ⚠ Error closing browser: {e}")


if __name__ == "__main__":
    print()
    print("VeoFlow Studio - Full Automation Test")
    print("This script tests the complete automated video generation flow")
    print()
    
    try:
        success = asyncio.run(test_full_automation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print("\n⚠ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

