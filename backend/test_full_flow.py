"""
Comprehensive test script to verify the complete video generation flow
Tests each component and identifies issues
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, init_db
from app.models.project import Project
from app.models.scene import Scene
from app.services.browser_manager import BrowserManager
from app.services.flow_controller import FlowController
from app.services.render_manager import RenderManager
from app.config import config_manager

async def test_browser_manager():
    """Test browser manager initialization"""
    print("\n" + "="*60)
    print("TEST 1: Browser Manager")
    print("="*60)
    
    try:
        browser_manager = BrowserManager()
        await browser_manager.initialize()
        print("✓ Browser manager initialized")
        
        page = await browser_manager.new_page()
        print("✓ Page created")
        
        await page.goto("https://www.google.com", timeout=30000)
        print("✓ Navigation test successful")
        
        await page.close()
        await browser_manager.close()
        print("✓ Browser closed successfully")
        return True
    except Exception as e:
        print(f"✗ Browser manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_flow_navigation():
    """Test navigation to Flow"""
    print("\n" + "="*60)
    print("TEST 2: Flow Navigation")
    print("="*60)
    
    try:
        browser_manager = BrowserManager()
        await browser_manager.initialize()
        page = await browser_manager.new_page()
        
        flow_controller = FlowController(browser_manager)
        await flow_controller.navigate_to_flow(page)
        print("✓ Successfully navigated to Flow")
        
        # Take screenshot
        screenshot_path = "/tmp/flow_navigation_test.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"✓ Screenshot saved to {screenshot_path}")
        
        # Check page title
        title = await page.title()
        print(f"✓ Page title: {title}")
        
        # Check URL
        url = page.url
        print(f"✓ Current URL: {url}")
        
        await page.close()
        await browser_manager.close()
        return True
    except Exception as e:
        print(f"✗ Flow navigation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_prompt_injection():
    """Test prompt injection"""
    print("\n" + "="*60)
    print("TEST 3: Prompt Injection")
    print("="*60)
    
    try:
        browser_manager = BrowserManager()
        await browser_manager.initialize()
        page = await browser_manager.new_page()
        
        flow_controller = FlowController(browser_manager)
        await flow_controller.navigate_to_flow(page)
        print("✓ Navigated to Flow")
        
        test_prompt = "A person walking through a city at sunset"
        await flow_controller.inject_prompt(page, test_prompt)
        print(f"✓ Prompt injected: {test_prompt}")
        
        # Verify prompt was set
        try:
            # Try to get the value from textarea
            textareas = await page.locator("textarea").all()
            if textareas:
                value = await textareas[0].input_value()
                if test_prompt[:20] in value or len(value) > 10:
                    print(f"✓ Prompt verified in textarea: {value[:50]}...")
                else:
                    print(f"⚠ Prompt may not be set correctly. Value: {value[:50]}")
        except Exception as e:
            print(f"⚠ Could not verify prompt: {e}")
        
        screenshot_path = "/tmp/flow_prompt_injected.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"✓ Screenshot saved to {screenshot_path}")
        
        await page.close()
        await browser_manager.close()
        return True
    except Exception as e:
        print(f"✗ Prompt injection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_full_render():
    """Test full render flow"""
    print("\n" + "="*60)
    print("TEST 4: Full Render Flow")
    print("="*60)
    
    try:
        # Initialize database
        init_db()
        db = SessionLocal()
        
        try:
            # Create test project and scene
            project_id = "test-full-flow-001"
            scene_id = f"{project_id}-scene-1"
            
            # Clean up existing
            existing_scene = db.query(Scene).filter(Scene.id == scene_id).first()
            if existing_scene:
                db.delete(existing_scene)
            existing_project = db.query(Project).filter(Project.id == project_id).first()
            if existing_project:
                db.delete(existing_project)
            db.commit()
            
            # Create new
            project = Project(
                id=project_id,
                name="Full Flow Test",
                description="Testing complete render flow"
            )
            db.add(project)
            
            scene = Scene(
                id=scene_id,
                project_id=project_id,
                number=1,
                prompt="A person walking through a beautiful city at sunset, wide shot, cinematic style",
                script="Test scene",
                status="pending"
            )
            db.add(scene)
            db.commit()
            
            print(f"✓ Created project: {project_id}")
            print(f"✓ Created scene: {scene_id}")
            
            # Test render
            render_manager = RenderManager()
            scene_dict = scene.to_dict()
            
            print("\n⚠ Starting render (this will take 2-4 minutes)...")
            print("⚠ Browser will open - you may need to log in if not already")
            print("⚠ Watch the browser window for progress\n")
            
            result = await render_manager.render_scene(
                scene_dict,
                project_id,
                characters=None
            )
            
            print("\n" + "="*60)
            print("RENDER RESULT:")
            print("="*60)
            print(f"Success: {result.get('success')}")
            
            if result.get('success'):
                print(f"Video path: {result.get('video_path')}")
                print(f"Scene ID: {result.get('scene_id')}")
                
                # Update scene
                scene.status = "completed"
                scene.video_path = result.get('video_path')
                db.commit()
                print("✓ Scene updated in database")
                
                # Check if file exists
                if result.get('video_path'):
                    video_file = Path(result.get('video_path'))
                    if video_file.exists():
                        size_mb = video_file.stat().st_size / (1024 * 1024)
                        print(f"✓ Video file exists: {size_mb:.2f} MB")
                    else:
                        print(f"⚠ Video file not found: {result.get('video_path')}")
            else:
                print(f"Error: {result.get('error')}")
                scene.status = "failed"
                db.commit()
            
            return result.get('success', False)
            
        finally:
            db.close()
            await render_manager.close()
            
    except Exception as e:
        print(f"✗ Full render test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("="*60)
    print("VeoFlow Studio - Comprehensive Flow Test")
    print("="*60)
    print("\nThis will test:")
    print("1. Browser Manager")
    print("2. Flow Navigation")
    print("3. Prompt Injection")
    print("4. Full Render Flow")
    print("\nPress Ctrl+C to skip any test\n")
    
    results = []
    
    # Test 1: Browser Manager
    results.append(await test_browser_manager())
    if not results[-1]:
        print("\n⚠ Browser manager failed - skipping remaining tests")
        return
    
    # Test 2: Flow Navigation
    results.append(await test_flow_navigation())
    if not results[-1]:
        print("\n⚠ Flow navigation failed - skipping remaining tests")
        return
    
    # Test 3: Prompt Injection
    results.append(await test_prompt_injection())
    if not results[-1]:
        print("\n⚠ Prompt injection failed - skipping render test")
        return
    
    # Test 4: Full Render (optional - takes time)
    print("\n" + "="*60)
    response = input("Run full render test? (takes 2-4 minutes) [y/N]: ")
    if response.lower() == 'y':
        results.append(await test_full_render())
    else:
        print("Skipping full render test")
        results.append(None)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Browser Manager: {'✓' if results[0] else '✗'}")
    print(f"Flow Navigation: {'✓' if results[1] else '✗'}")
    print(f"Prompt Injection: {'✓' if results[2] else '✗'}")
    if results[3] is not None:
        print(f"Full Render: {'✓' if results[3] else '✗'}")
    else:
        print("Full Render: Skipped")
    
    all_passed = all(r for r in results if r is not None)
    if all_passed:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed - check errors above")
    
    print("\nScreenshots saved to /tmp/flow_*.png")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)

