"""
Test script to verify video rendering works end-to-end
"""

import asyncio
import sys
import os
from app.core.database import SessionLocal, init_db
from app.models.project import Project
from app.models.scene import Scene
from app.services.render_manager import RenderManager

async def test_render():
    """Test rendering a single scene"""
    
    print("=" * 60)
    print("VeoFlow Studio - Render Test")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    db = SessionLocal()
    
    try:
        # Get or create test project
        test_project_id = "test-render-001"
        project = db.query(Project).filter(Project.id == test_project_id).first()
        
        if not project:
            project = Project(
                id=test_project_id,
                name="Render Test Project",
                description="Testing video rendering"
            )
            db.add(project)
            db.commit()
            print(f"   ✓ Created project: {project.id}")
        else:
            print(f"   ✓ Using existing project: {project.id}")
        
        # Get or create test scene
        scene = db.query(Scene).filter(
            Scene.project_id == test_project_id,
            Scene.number == 1
        ).first()
        
        if not scene:
            scene = Scene(
                id=f"{test_project_id}-scene-1",
                project_id=test_project_id,
                number=1,
                prompt="A person walking through a beautiful city at sunset, wide shot, cinematic style",
                script="Test scene",
                status="pending"
            )
            db.add(scene)
            db.commit()
            print(f"   ✓ Created scene: {scene.id}")
        else:
            print(f"   ✓ Using existing scene: {scene.id}")
        
        # Test render
        print("\n2. Testing video rendering...")
        print(f"   Scene prompt: {scene.prompt}")
        print("   This will open a browser window...")
        
        render_manager = RenderManager()
        
        scene_dict = {
            "id": scene.id,
            "prompt": scene.prompt,
            "number": scene.number
        }
        
        print("\n3. Starting render (this may take 2-4 minutes)...")
        result = await render_manager.render_scene(
            scene_dict,
            test_project_id,
            characters=None
        )
        
        print("\n4. Render result:")
        print(f"   Success: {result.get('success')}")
        
        if result.get('success'):
            print(f"   Video path: {result.get('video_path')}")
            print(f"   Scene ID: {result.get('scene_id')}")
            
            # Update scene in database
            scene.status = "completed"
            scene.video_path = result.get('video_path')
            db.commit()
            print("\n   ✓ Scene updated in database")
        else:
            print(f"   Error: {result.get('error')}")
            scene.status = "failed"
            db.commit()
        
        print("\n" + "=" * 60)
        if result.get('success'):
            print("✓ Render test completed successfully!")
        else:
            print("✗ Render test failed - check error message above")
        print("=" * 60)
        
        return result.get('success', False)
    
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()
        # Cleanup render manager
        try:
            await render_manager.close()
        except:
            pass


if __name__ == "__main__":
    success = asyncio.run(test_render())
    sys.exit(0 if success else 1)

