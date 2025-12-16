"""
Projects API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
from app.core.database import get_db
from app.models.project import Project
from app.models.scene import Scene

logger = logging.getLogger(__name__)
from app.services.script_generator import ScriptGenerator
from app.services.scene_builder import SceneBuilder
from app.services.video_processor import VideoProcessor
from app.services.character_generator import CharacterGenerator
from app.services.scene_prompt_generator import ScenePromptGenerator
from app.models.script import Script
from app.models.character import CharacterDNA
import uuid
import os
from pathlib import Path

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class RenderSettings(BaseModel):
    aspect_ratio: Optional[str] = None  # "16:9" or "9:16"
    videos_per_scene: Optional[int] = None  # 1, 2, 3, or 4
    model: Optional[str] = None  # "veo3.1-fast" or other model names


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    script: Optional[str] = None
    render_settings: Optional[RenderSettings] = None


class ScriptGenerateRequest(BaseModel):
    prompt: str


class ScriptGenerateFromParametersRequest(BaseModel):
    main_content: str
    video_duration: int
    style: str
    target_audience: str
    aspect_ratio: str
    language: Optional[str] = None
    voice_style: Optional[str] = None
    music_style: Optional[str] = None
    color_palette: Optional[str] = None
    transition_style: Optional[str] = None


class StitchRequest(BaseModel):
    transition: str = "fade"
    transition_duration: float = 0.5


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    script: Optional[str] = None
    metadata: Optional[dict] = None
    render_settings: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project with default render settings"""
    project = Project(
        id=str(uuid.uuid4()),
        name=project_data.name,
        description=project_data.description
    )
    # Initialize with default render settings
    project.update_render_settings(
        aspect_ratio="16:9",
        videos_per_scene=2,
        model="veo3.1-fast"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project.to_dict()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    """List all projects"""
    projects = db.query(Project).all()
    return [p.to_dict() for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@router.post("/{project_id}/generate-script")
async def generate_script(
    project_id: str,
    request: ScriptGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate script and scenes from prompt"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Generate script
    script_generator = ScriptGenerator()
    result = await script_generator.generate_script(request.prompt)
    
    # Update project with script
    project.script = result["text"]
    project.project_metadata = result.get("metadata", {})
    db.commit()
    
    # Create scenes
    scene_builder = SceneBuilder()
    optimized_scenes = scene_builder.build_scene_prompts(
        result["scenes"],
        result.get("characters", []),
        result.get("metadata", {}).get("cinematicStyle")
    )
    
    # Delete existing scenes
    db.query(Scene).filter(Scene.project_id == project_id).delete()
    
    # Create new scenes
    created_scenes = []
    for scene_data in optimized_scenes:
        scene = Scene(
            id=str(uuid.uuid4()),
            project_id=project_id,
            number=scene_data["number"],
            prompt=scene_data["prompt"],
            script=scene_data.get("script", ""),
            status="pending"
        )
        db.add(scene)
        created_scenes.append(scene.to_dict())
    
    db.commit()
    
    return {
        "script": result["text"],
        "scenes": created_scenes,
        "characters": result.get("characters", []),
        "metadata": result.get("metadata", {})
    }


@router.post("/{project_id}/generate-script-from-parameters")
async def generate_script_from_parameters(
    project_id: str,
    request: ScriptGenerateFromParametersRequest,
    db: Session = Depends(get_db)
):
    """Generate complete script, characters, and scenes from parameters"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Step 1: Generate script
        script_generator = ScriptGenerator()
        script_result = await script_generator.generate_script_from_parameters(
            main_content=request.main_content,
            video_duration=request.video_duration,
            style=request.style,
            target_audience=request.target_audience,
            aspect_ratio=request.aspect_ratio,
            language=request.language,
            voice_style=request.voice_style,
            music_style=request.music_style,
            color_palette=request.color_palette,
            transition_style=request.transition_style
        )
        
        # Step 2: Create or update Script model
        existing_script = db.query(Script).filter(Script.project_id == project_id).first()
        if existing_script:
            # Update existing script
            existing_script.main_content = request.main_content
            existing_script.video_duration = request.video_duration
            existing_script.style = request.style
            existing_script.target_audience = request.target_audience
            existing_script.aspect_ratio = request.aspect_ratio
            existing_script.language = request.language
            existing_script.voice_style = request.voice_style
            existing_script.music_style = request.music_style
            existing_script.color_palette = request.color_palette
            existing_script.transition_style = request.transition_style
            existing_script.full_script = script_result["text"]
            existing_script.story_structure = script_result.get("story_structure", {})
            existing_script.scene_count = script_result.get("scene_count", 0)
            script = existing_script
        else:
            # Create new script
            script = Script(
                id=str(uuid.uuid4()),
                project_id=project_id,
                main_content=request.main_content,
                video_duration=request.video_duration,
                style=request.style,
                target_audience=request.target_audience,
                aspect_ratio=request.aspect_ratio,
                language=request.language,
                voice_style=request.voice_style,
                music_style=request.music_style,
                color_palette=request.color_palette,
                transition_style=request.transition_style,
                full_script=script_result["text"],
                story_structure=script_result.get("story_structure", {}),
                scene_count=script_result.get("scene_count", 0)
            )
            db.add(script)
        
        db.commit()
        db.refresh(script)
        
        # Step 3: Generate Character DNA for all characters
        character_generator = CharacterGenerator()
        character_dna_list = []
        
        for char_data in script_result.get("characters", []):
            char_name = char_data.get("name", "")
            char_description = char_data.get("description", "")
            
            if not char_name:
                continue
            
            try:
                char_dna = await character_generator.generate_character_dna(
                    character_name=char_name,
                    character_description=char_description,
                    script_context=script_result["text"],
                    style=request.style,
                    target_audience=request.target_audience
                )
                
                # Create or update Character DNA in database
                existing_char = db.query(CharacterDNA).filter(
                    CharacterDNA.project_id == project_id,
                    CharacterDNA.name == char_name
                ).first()
                
                if existing_char:
                    # Update existing character
                    for key, value in char_dna.items():
                        if hasattr(existing_char, key):
                            setattr(existing_char, key, value)
                    char_db = existing_char
                else:
                    # Create new character
                    from app.services.character_manager import CharacterManager
                    char_manager = CharacterManager()
                    consistency_seed = char_manager.generate_consistency_seed(char_dna)
                    
                    char_db = CharacterDNA(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        name=char_dna.get("name", char_name),
                        gender=char_dna.get("gender", "unknown"),
                        age=None,  # Keep as None, use age_description
                        age_description=char_dna.get("age_description", ""),
                        species=char_dna.get("species", ""),
                        voice_personality=char_dna.get("voice_personality", ""),
                        body_build=char_dna.get("body_build", ""),
                        face_shape=char_dna.get("face_shape", ""),
                        hair=char_dna.get("hair", ""),
                        skin_or_fur_color=char_dna.get("skin_or_fur_color", ""),
                        signature_feature=char_dna.get("signature_feature", ""),
                        outfit_top=char_dna.get("outfit_top", ""),
                        outfit_bottom=char_dna.get("outfit_bottom", ""),
                        helmet_or_hat=char_dna.get("helmet_or_hat", ""),
                        shoes_or_footwear=char_dna.get("shoes_or_footwear", ""),
                        props=char_dna.get("props", []),
                        body_metrics=char_dna.get("body_metrics", {}),
                        consistency_seed=consistency_seed
                    )
                    db.add(char_db)
                
                db.commit()
                db.refresh(char_db)
                character_dna_list.append(char_db.to_dict())
                
            except Exception as e:
                logger.error(f"Failed to generate character DNA for {char_name}: {e}")
                continue
        
        # Step 4: Generate detailed scene prompts
        scene_prompt_generator = ScenePromptGenerator()
        detailed_scenes = await scene_prompt_generator.generate_scene_prompts(
            script_scenes=script_result.get("scenes", []),
            character_dna_list=character_dna_list,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            target_audience=request.target_audience
        )
        
        # Step 5: Delete existing scenes and create new ones
        db.query(Scene).filter(Scene.project_id == project_id).delete()
        
        created_scenes = []
        for scene_data in detailed_scenes:
            scene = Scene(
                id=str(uuid.uuid4()),
                project_id=project_id,
                number=scene_data.get("scene_number", 1),
                prompt=scene_data.get("prompt", ""),
                script=scene_data.get("script", ""),
                scene_description=scene_data.get("scene_description", ""),
                duration_sec=scene_data.get("duration_sec", 30),
                visual_style=scene_data.get("visual_style", ""),
                environment=scene_data.get("environment", ""),
                camera_angle=scene_data.get("camera_angle", ""),
                character_adaptations=scene_data.get("character_adaptations", {}),
                status="pending"
            )
            db.add(scene)
            created_scenes.append(scene.to_dict())
        
        db.commit()
        
        return {
            "script_id": script.id,
            "scenes": created_scenes,
            "characters": character_dna_list,
            "total_duration": request.video_duration,
            "scene_count": len(created_scenes)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate script from parameters: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate script: {str(e)}")


@router.post("/{project_id}/stitch")
async def stitch_videos(
    project_id: str,
    request: StitchRequest,
    db: Session = Depends(get_db)
):
    """Stitch all completed scene videos into final video"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all completed scenes
    scenes = db.query(Scene).filter(
        Scene.project_id == project_id,
        Scene.status == "completed"
    ).order_by(Scene.number).all()
    
    if not scenes:
        raise HTTPException(status_code=400, detail="No completed scenes to stitch")
    
    # Get video paths
    scene_paths = [s.video_path for s in scenes if s.video_path and os.path.exists(s.video_path)]
    
    if not scene_paths:
        raise HTTPException(status_code=400, detail="No valid video files found")
    
    # Create output path
    from app.config import DOWNLOADS_PATH
    output_dir = os.path.join(DOWNLOADS_PATH, project_id)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"final_{project_id}.mp4")
    
    # Stitch videos
    processor = VideoProcessor()
    final_path = processor.stitch_scenes(
        scene_paths,
        output_path,
        request.transition,
        request.transition_duration
    )
    
    return {
        "video_path": final_path,
        "scenes_count": len(scene_paths)
    }


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.script is not None:
        project.script = project_data.script
    
    # Update render settings if provided
    if project_data.render_settings is not None:
        render_settings_dict = project_data.render_settings.dict(exclude_unset=True)
        if render_settings_dict:
            project.update_render_settings(**render_settings_dict)
    
    db.commit()
    db.refresh(project)
    return project.to_dict()


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}
