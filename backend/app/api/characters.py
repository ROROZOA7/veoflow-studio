"""
Characters API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.character import CharacterDNA
from app.services.character_manager import CharacterManager
import uuid

router = APIRouter()
character_manager = CharacterManager()


class CharacterCreate(BaseModel):
    project_id: str
    name: str
    gender: str
    age: int = None
    face: dict = None
    hair: dict = None
    body: dict = None
    clothing: dict = None
    personality: dict = None


class CharacterUpdate(BaseModel):
    name: str = None
    gender: str = None
    age: int = None
    face: dict = None
    hair: dict = None
    body: dict = None
    clothing: dict = None
    personality: dict = None


class CharacterResponse(BaseModel):
    id: str
    project_id: str
    name: str
    gender: str
    age: int = None
    face: dict = None
    hair: dict = None
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
        face=character_data.face or {},
        hair=character_data.hair or {},
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

