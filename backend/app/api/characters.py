"""
Characters API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.character import CharacterDNA
from app.models.project import Project
from app.services.character_manager import CharacterManager
from app.services.character_generator import CharacterGenerator
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
character_manager = CharacterManager()


class CharacterCreate(BaseModel):
    project_id: str
    name: str
    gender: str
    age: int = None
    age_description: str = None
    species: str = None
    voice_personality: str = None
    body_build: str = None
    face_shape: str = None
    hair: str = None
    skin_or_fur_color: str = None
    signature_feature: str = None
    outfit_top: str = None
    outfit_bottom: str = None
    helmet_or_hat: str = None
    shoes_or_footwear: str = None
    props: list = None
    body_metrics: dict = None
    position: str = None
    orientation: str = None
    pose: str = None
    foot_placement: str = None
    hand_detail: str = None
    expression: str = None
    action_flow: dict = None
    face: dict = None
    body: dict = None
    clothing: dict = None
    personality: dict = None


class CharacterUpdate(BaseModel):
    name: str = None
    gender: str = None
    age: int = None
    age_description: str = None
    species: str = None
    voice_personality: str = None
    body_build: str = None
    face_shape: str = None
    hair: str = None
    skin_or_fur_color: str = None
    signature_feature: str = None
    outfit_top: str = None
    outfit_bottom: str = None
    helmet_or_hat: str = None
    shoes_or_footwear: str = None
    props: list = None
    body_metrics: dict = None
    position: str = None
    orientation: str = None
    pose: str = None
    foot_placement: str = None
    hand_detail: str = None
    expression: str = None
    action_flow: dict = None
    face: dict = None
    body: dict = None
    clothing: dict = None
    personality: dict = None


class CharacterGenerateRequest(BaseModel):
    character_name: str
    character_description: str
    script_context: str
    style: str
    target_audience: str


class CharacterResponse(BaseModel):
    id: str
    project_id: str
    name: str
    gender: str
    age: int = None
    age_description: str = None
    species: str = None
    voice_personality: str = None
    body_build: str = None
    face_shape: str = None
    hair: str = None
    skin_or_fur_color: str = None
    signature_feature: str = None
    outfit_top: str = None
    outfit_bottom: str = None
    helmet_or_hat: str = None
    shoes_or_footwear: str = None
    props: list = None
    body_metrics: dict = None
    position: str = None
    orientation: str = None
    pose: str = None
    foot_placement: str = None
    hand_detail: str = None
    expression: str = None
    action_flow: dict = None
    face: dict = None
    body: dict = None
    clothing: dict = None
    personality: dict = None
    consistency_seed: str = None
    metadata: dict = None
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[CharacterResponse])
async def list_characters(
    project_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List characters, optionally filtered by project"""
    query = db.query(CharacterDNA)
    if project_id:
        query = query.filter(CharacterDNA.project_id == project_id)
    characters = query.all()
    return [c.to_dict() for c in characters]


@router.post("/projects/{project_id}/generate", response_model=CharacterResponse)
async def generate_character(
    project_id: str,
    request: CharacterGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate character DNA using AI"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        character_generator = CharacterGenerator()
        char_dna = await character_generator.generate_character_dna(
            character_name=request.character_name,
            character_description=request.character_description,
            script_context=request.script_context,
            style=request.style,
            target_audience=request.target_audience
        )
        
        # Create character in database
        consistency_seed = character_manager.generate_consistency_seed(char_dna)
        
        character = CharacterDNA(
            id=str(uuid.uuid4()),
            project_id=project_id,
            name=char_dna.get("name", request.character_name),
            gender=char_dna.get("gender", "unknown"),
            age=None,
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
        db.add(character)
        db.commit()
        db.refresh(character)
        return character.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to generate character: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate character: {str(e)}")


@router.post("", response_model=CharacterResponse)
async def create_character(
    character_data: CharacterCreate,
    db: Session = Depends(get_db)
):
    """Create a new character"""
    # Generate consistency seed
    char_dict = character_data.dict(exclude_none=True)
    consistency_seed = character_manager.generate_consistency_seed(char_dict)
    
    character = CharacterDNA(
        id=str(uuid.uuid4()),
        project_id=character_data.project_id,
        name=character_data.name,
        gender=character_data.gender,
        age=character_data.age,
        age_description=character_data.age_description,
        species=character_data.species,
        voice_personality=character_data.voice_personality,
        body_build=character_data.body_build,
        face_shape=character_data.face_shape,
        hair=character_data.hair,
        skin_or_fur_color=character_data.skin_or_fur_color,
        signature_feature=character_data.signature_feature,
        outfit_top=character_data.outfit_top,
        outfit_bottom=character_data.outfit_bottom,
        helmet_or_hat=character_data.helmet_or_hat,
        shoes_or_footwear=character_data.shoes_or_footwear,
        props=character_data.props or [],
        body_metrics=character_data.body_metrics or {},
        position=character_data.position,
        orientation=character_data.orientation,
        pose=character_data.pose,
        foot_placement=character_data.foot_placement,
        hand_detail=character_data.hand_detail,
        expression=character_data.expression,
        action_flow=character_data.action_flow or {},
        face=character_data.face or {},
        body=character_data.body or {},
        clothing=character_data.clothing or {},
        personality=character_data.personality or {},
        consistency_seed=consistency_seed
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    return character.to_dict()


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: str, db: Session = Depends(get_db)):
    """Get a character by ID"""
    character = db.query(CharacterDNA).filter(CharacterDNA.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character.to_dict()


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    character_data: CharacterUpdate,
    db: Session = Depends(get_db)
):
    """Update a character"""
    character = db.query(CharacterDNA).filter(CharacterDNA.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Update fields
    update_data = character_data.dict(exclude_none=True)
    for key, value in update_data.items():
        if hasattr(character, key):
            setattr(character, key, value)
    
    # Regenerate consistency seed
    char_dict = character.to_dict()
    character.consistency_seed = character_manager.generate_consistency_seed(char_dict)
    
    db.commit()
    db.refresh(character)
    return character.to_dict()


@router.delete("/{character_id}")
async def delete_character(character_id: str, db: Session = Depends(get_db)):
    """Delete a character"""
    character = db.query(CharacterDNA).filter(CharacterDNA.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    db.delete(character)
    db.commit()
    return {"message": "Character deleted"}

