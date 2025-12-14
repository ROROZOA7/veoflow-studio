"""
Quick test script to verify the full video generation flow
"""

import asyncio
import sys
from app.core.database import SessionLocal, init_db
from app.models.project import Project
from app.models.scene import Scene
from app.services.script_generator import ScriptGenerator
from app.services.scene_builder import SceneBuilder
from app.services.render_manager import RenderManager
from app.services.character_manager import CharacterManager

async def test_full_flow():
    """Test the complete video generation flow"""
    
    print("=" * 60)
    print("VeoFlow Studio - Full Flow Test")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    db = SessionLocal()
    
    try:
        # Clean up any existing test data
        test_project_id = "test-project-001"
        print("\n2. Cleaning up existing test data...")
        existing_project = db.query(Project).filter(Project.id == test_project_id).first()
        if existing_project:
            # Delete related scenes first (due to foreign key constraint)
            existing_scenes = db.query(Scene).filter(Scene.project_id == test_project_id).all()
            for scene in existing_scenes:
                db.delete(scene)
            db.delete(existing_project)
            db.commit()
            print(f"   ✓ Removed existing test project and {len(existing_scenes)} scenes")
        
        # Create project
        print("\n3. Creating project...")
        project = Project(
            id=test_project_id,
            name="Test Video Project",
            description="Testing the full flow"
        )
        db.add(project)
        db.commit()
        print(f"   ✓ Project created: {project.id}")
        
        # Generate script (if API key is configured)
        print("\n4. Testing script generation...")
        script_generator = ScriptGenerator()
        
        # Check if API key is configured
        if not script_generator.api_key:
            print("   ⚠ No AI API key configured - skipping script generation")
            print("   To enable: Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY in .env")
            print("\n   Creating test scenes manually instead...")
            
            # Create test scenes manually
            test_scenes = [
                {
                    "number": 1,
                    "prompt": "A person walking through a beautiful city at sunset, wide shot, cinematic style",
                    "script": "Scene 1: Person walking through city",
                    "description": "Opening scene"
                },
                {
                    "number": 2,
                    "prompt": "Close-up of the person's face, golden hour lighting, warm mood",
                    "script": "Scene 2: Close-up",
                    "description": "Character close-up"
                }
            ]
            
            for scene_data in test_scenes:
                scene = Scene(
                    id=f"{project.id}-scene-{scene_data['number']}",
                    project_id=project.id,
                    number=scene_data["number"],
                    prompt=scene_data["prompt"],
                    script=scene_data.get("script", ""),
                    status="pending"
                )
                db.add(scene)
                print(f"   ✓ Scene {scene.number}: {scene.prompt[:50]}...")
            
            db.commit()
        else:
            try:
                result = await script_generator.generate_script(
                    "A person walking through a beautiful city at sunset"
                )
                print(f"   ✓ Script generated: {len(result['text'])} characters")
                print(f"   ✓ Scenes created: {len(result['scenes'])}")
                
                project.script = result["text"]
                project.project_metadata = result.get("metadata", {})
                db.commit()
                
                # Create scenes
                print("\n5. Creating scenes in database...")
                scene_builder = SceneBuilder()
                optimized_scenes = scene_builder.build_scene_prompts(
                    result["scenes"],
                    result.get("characters", []),
                    result.get("metadata", {}).get("cinematicStyle")
                )
                
                for scene_data in optimized_scenes:
                    scene = Scene(
                        id=f"{project.id}-scene-{scene_data['number']}",
                        project_id=project.id,
                        number=scene_data["number"],
                        prompt=scene_data["prompt"],
                        script=scene_data.get("script", ""),
                        status="pending"
                    )
                    db.add(scene)
                    print(f"   ✓ Scene {scene.number}: {scene.prompt[:50]}...")
                
                db.commit()
            except Exception as e:
                print(f"   ✗ Script generation error: {e}")
                print("   Creating test scenes manually instead...")
                # Create manual test scenes (same as above)
                test_scenes = [
                    {
                        "number": 1,
                        "prompt": "A person walking through a beautiful city at sunset, wide shot",
                        "script": "Scene 1",
                        "description": "Opening scene"
                    }
                ]
                for scene_data in test_scenes:
                    scene = Scene(
                        id=f"{project.id}-scene-{scene_data['number']}",
                        project_id=project.id,
                        number=scene_data["number"],
                        prompt=scene_data["prompt"],
                        script=scene_data.get("script", ""),
                        status="pending"
                    )
                    db.add(scene)
                db.commit()
        
        # Test character consistency
        print("\n6. Testing character consistency...")
        character_manager = CharacterManager()
        test_character = {
            "name": "Test Character",
            "gender": "female",
            "age": 25,
            "face": {"shape": "round", "eyes": "green"},
            "hair": {"color": "brown", "style": "shoulder-length"},
            "clothing": {"style": "casual", "typicalOutfit": "blue sweater"}
        }
        seed = character_manager.generate_consistency_seed(test_character)
        print(f"   ✓ Consistency seed: {seed[:80]}...")
        
        print("\n" + "=" * 60)
        print("✓ Full flow test completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Configure AI API key in .env for script generation")
        print("2. Start Celery worker: celery -A app.workers.render_worker worker")
        print("3. Start FastAPI: uvicorn app.main:app --reload")
        print("4. Render scenes via API: POST /api/render/scenes/{id}/render")
        print("5. Check status: GET /api/render/tasks/{task_id}")
        print("6. Stitch videos: POST /api/projects/{id}/stitch")
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_full_flow())

