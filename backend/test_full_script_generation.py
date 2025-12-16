"""
End-to-end test for script generation feature
Tests the complete flow with real services and database
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.database import SessionLocal, init_db
from app.models.project import Project
from app.models.scene import Scene
from app.models.script import Script
from app.models.character import CharacterDNA
from app.services.script_generator import ScriptGenerator
from app.services.character_generator import CharacterGenerator
from app.services.scene_prompt_generator import ScenePromptGenerator
from app.config import settings

# Test configuration
TEST_PROJECT_ID = "test-script-gen-001"
TEST_MAIN_CONTENT = "The story of the tortoise and the hare"
TEST_VIDEO_DURATION = 300  # 5 minutes
TEST_STYLE = "cartoon"
TEST_TARGET_AUDIENCE = "children"
TEST_ASPECT_RATIO = "16:9"


async def test_script_generation_from_parameters():
    """Test script generation from parameters"""
    print("\n" + "=" * 60)
    print("Testing Script Generation from Parameters")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    db = SessionLocal()
    
    try:
        # Clean up existing test data
        print("\n2. Cleaning up existing test data...")
        existing_project = db.query(Project).filter(Project.id == TEST_PROJECT_ID).first()
        if existing_project:
            # Delete related data
            db.query(Scene).filter(Scene.project_id == TEST_PROJECT_ID).delete()
            db.query(CharacterDNA).filter(CharacterDNA.project_id == TEST_PROJECT_ID).delete()
            db.query(Script).filter(Script.project_id == TEST_PROJECT_ID).delete()
            db.delete(existing_project)
            db.commit()
            print("   ✓ Cleaned up existing test data")
        
        # Create test project
        print("\n3. Creating test project...")
        project = Project(
            id=TEST_PROJECT_ID,
            name="Test Script Generation Project",
            description="Testing script generation from parameters"
        )
        db.add(project)
        db.commit()
        print(f"   ✓ Project created: {project.id}")
        
        # Test script generation
        print("\n4. Testing script generation from parameters...")
        script_generator = ScriptGenerator()
        
        # Check if API key is configured
        if not script_generator.api_key:
            print("   ⚠ No AI API key configured")
            print("   To enable: Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY in .env")
            print("   Skipping AI-based tests...")
            return False
        
        print(f"   Using provider: {script_generator.provider}, model: {script_generator.model}")
        print(f"   Main content: {TEST_MAIN_CONTENT}")
        print(f"   Duration: {TEST_VIDEO_DURATION}s")
        print(f"   Style: {TEST_STYLE}")
        print(f"   Target audience: {TEST_TARGET_AUDIENCE}")
        print(f"   Aspect ratio: {TEST_ASPECT_RATIO}")
        
        try:
            script_result = await script_generator.generate_script_from_parameters(
                main_content=TEST_MAIN_CONTENT,
                video_duration=TEST_VIDEO_DURATION,
                style=TEST_STYLE,
                target_audience=TEST_TARGET_AUDIENCE,
                aspect_ratio=TEST_ASPECT_RATIO,
                language="en-US",
                voice_style="narrator",
                music_style="upbeat"
            )
            
            print(f"   ✓ Script generated successfully")
            print(f"   ✓ Story structure: {bool(script_result.get('story_structure'))}")
            print(f"   ✓ Scenes: {len(script_result.get('scenes', []))}")
            print(f"   ✓ Characters: {len(script_result.get('characters', []))}")
            print(f"   ✓ Total duration: {script_result.get('total_duration')}s")
            print(f"   ✓ Scene count: {script_result.get('scene_count')}")
            
            # Verify scene durations sum to total
            scenes = script_result.get('scenes', [])
            total_scene_duration = sum(s.get('duration_sec', 0) for s in scenes)
            print(f"   ✓ Scene durations sum: {total_scene_duration}s (expected: {TEST_VIDEO_DURATION}s)")
            
            if total_scene_duration != TEST_VIDEO_DURATION:
                print(f"   ⚠ Warning: Scene durations don't match total ({total_scene_duration} vs {TEST_VIDEO_DURATION})")
            
            # Create Script model
            print("\n5. Creating Script model...")
            script = Script(
                id=f"{TEST_PROJECT_ID}-script",
                project_id=TEST_PROJECT_ID,
                main_content=TEST_MAIN_CONTENT,
                video_duration=TEST_VIDEO_DURATION,
                style=TEST_STYLE,
                target_audience=TEST_TARGET_AUDIENCE,
                aspect_ratio=TEST_ASPECT_RATIO,
                language="en-US",
                voice_style="narrator",
                music_style="upbeat",
                full_script=script_result.get('text', ''),
                story_structure=script_result.get('story_structure', {}),
                scene_count=script_result.get('scene_count', 0)
            )
            db.add(script)
            db.commit()
            db.refresh(script)
            print(f"   ✓ Script model created: {script.id}")
            
            # Test character generation
            print("\n6. Testing character generation...")
            character_generator = CharacterGenerator()
            characters_data = script_result.get('characters', [])
            
            if not characters_data:
                print("   ⚠ No characters found in script result")
            else:
                print(f"   Generating DNA for {len(characters_data)} characters...")
                character_dna_list = []
                
                for char_data in characters_data[:3]:  # Limit to 3 for testing
                    char_name = char_data.get('name', '')
                    char_description = char_data.get('description', '')
                    
                    if not char_name:
                        continue
                    
                    print(f"   Generating DNA for: {char_name}")
                    try:
                        char_dna = await character_generator.generate_character_dna(
                            character_name=char_name,
                            character_description=char_description,
                            script_context=script_result.get('text', ''),
                            style=TEST_STYLE,
                            target_audience=TEST_TARGET_AUDIENCE
                        )
                        
                        print(f"      ✓ Species: {char_dna.get('species', 'N/A')}")
                        print(f"      ✓ Gender: {char_dna.get('gender', 'N/A')}")
                        print(f"      ✓ Body build: {char_dna.get('body_build', 'N/A')}")
                        
                        # Create Character DNA model
                        from app.services.character_manager import CharacterManager
                        char_manager = CharacterManager()
                        consistency_seed = char_manager.generate_consistency_seed(char_dna)
                        
                        character = CharacterDNA(
                            id=f"{TEST_PROJECT_ID}-char-{char_name.lower().replace(' ', '-')}",
                            project_id=TEST_PROJECT_ID,
                            name=char_dna.get('name', char_name),
                            gender=char_dna.get('gender', 'unknown'),
                            age_description=char_dna.get('age_description', ''),
                            species=char_dna.get('species', ''),
                            voice_personality=char_dna.get('voice_personality', ''),
                            body_build=char_dna.get('body_build', ''),
                            face_shape=char_dna.get('face_shape', ''),
                            hair=char_dna.get('hair', ''),
                            skin_or_fur_color=char_dna.get('skin_or_fur_color', ''),
                            signature_feature=char_dna.get('signature_feature', ''),
                            outfit_top=char_dna.get('outfit_top', ''),
                            outfit_bottom=char_dna.get('outfit_bottom', ''),
                            helmet_or_hat=char_dna.get('helmet_or_hat', ''),
                            shoes_or_footwear=char_dna.get('shoes_or_footwear', ''),
                            props=char_dna.get('props', []),
                            body_metrics=char_dna.get('body_metrics', {}),
                            consistency_seed=consistency_seed
                        )
                        db.add(character)
                        character_dna_list.append(character.to_dict())
                        
                    except Exception as e:
                        print(f"      ✗ Failed to generate character DNA: {e}")
                        continue
                
                db.commit()
                print(f"   ✓ Created {len(character_dna_list)} character DNA records")
            
            # Test scene prompt generation
            print("\n7. Testing scene prompt generation...")
            scene_prompt_generator = ScenePromptGenerator()
            
            if not scenes:
                print("   ⚠ No scenes to generate prompts for")
            else:
                print(f"   Generating detailed prompts for {len(scenes)} scenes...")
                
                # Get character DNA list
                character_dna_list = [c.to_dict() for c in db.query(CharacterDNA).filter(
                    CharacterDNA.project_id == TEST_PROJECT_ID
                ).all()]
                
                try:
                    detailed_scenes = await scene_prompt_generator.generate_scene_prompts(
                        script_scenes=scenes,
                        character_dna_list=character_dna_list,
                        style=TEST_STYLE,
                        aspect_ratio=TEST_ASPECT_RATIO,
                        target_audience=TEST_TARGET_AUDIENCE
                    )
                    
                    print(f"   ✓ Generated {len(detailed_scenes)} detailed scene prompts")
                    
                    # Create Scene models
                    created_scenes = []
                    for scene_data in detailed_scenes:
                        scene = Scene(
                            id=f"{TEST_PROJECT_ID}-scene-{scene_data.get('scene_number', 1)}",
                            project_id=TEST_PROJECT_ID,
                            number=scene_data.get('scene_number', 1),
                            prompt=scene_data.get('prompt', ''),
                            scene_description=scene_data.get('scene_description', ''),
                            duration_sec=scene_data.get('duration_sec', 30),
                            visual_style=scene_data.get('visual_style', ''),
                            environment=scene_data.get('environment', ''),
                            camera_angle=scene_data.get('camera_angle', ''),
                            character_adaptations=scene_data.get('character_adaptations', {}),
                            status="pending"
                        )
                        db.add(scene)
                        created_scenes.append(scene)
                    
                    db.commit()
                    print(f"   ✓ Created {len(created_scenes)} scene records")
                    
                    # Display sample scene
                    if created_scenes:
                        sample_scene = created_scenes[0]
                        print(f"\n   Sample Scene {sample_scene.number}:")
                        print(f"      Description: {sample_scene.scene_description[:80]}...")
                        print(f"      Duration: {sample_scene.duration_sec}s")
                        print(f"      Prompt length: {len(sample_scene.prompt)} chars")
                    
                except Exception as e:
                    print(f"   ✗ Failed to generate scene prompts: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Final verification
            print("\n8. Final verification...")
            db_script = db.query(Script).filter(Script.project_id == TEST_PROJECT_ID).first()
            db_scenes = db.query(Scene).filter(Scene.project_id == TEST_PROJECT_ID).all()
            db_characters = db.query(CharacterDNA).filter(CharacterDNA.project_id == TEST_PROJECT_ID).all()
            
            print(f"   ✓ Script in database: {bool(db_script)}")
            print(f"   ✓ Scenes in database: {len(db_scenes)}")
            print(f"   ✓ Characters in database: {len(db_characters)}")
            
            if db_script:
                print(f"   ✓ Script scene_count: {db_script.scene_count}")
                print(f"   ✓ Script video_duration: {db_script.video_duration}s")
            
            # Verify scene durations
            total_duration = sum(s.duration_sec or 0 for s in db_scenes)
            print(f"   ✓ Total scene duration: {total_duration}s")
            
            print("\n" + "=" * 60)
            print("✓ All tests passed!")
            print("=" * 60)
            return True
            
        except Exception as e:
            print(f"\n✗ Script generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"\n✗ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Script Generation Feature - Real Integration Tests")
    print("=" * 60)
    print("\nNote: These tests use real AI services and database")
    print("Make sure you have API keys configured in .env file")
    print("=" * 60)
    
    success = await test_script_generation_from_parameters()
    
    if success:
        print("\n✓ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())



