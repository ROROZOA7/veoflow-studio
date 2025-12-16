"""
Character database model
"""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class CharacterDNA(Base):
    """Character DNA model for maintaining character consistency"""
    
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    gender = Column(String, nullable=False)  # male, female, non-binary, other
    age = Column(Integer, nullable=True)  # Keep as Integer for backward compatibility
    age_description = Column(String, nullable=True)  # e.g., "Mature", "Young" - descriptive age
    
    # New detailed fields from template
    species = Column(String, nullable=True)  # e.g., "Rabbit - White Rabbit"
    voice_personality = Column(Text, nullable=True)  # e.g., "Gentle, clear; gender=Male; locale=vi-VN"
    body_build = Column(String, nullable=True)  # e.g., "Chubby, soft"
    face_shape = Column(String, nullable=True)  # e.g., "Round"
    hair = Column(String, nullable=True)  # e.g., "White fur" (keeping JSON for backward compat)
    skin_or_fur_color = Column(String, nullable=True)  # e.g., "Soft white fur"
    signature_feature = Column(Text, nullable=True)  # e.g., "Round glasses; gentle, warm smile"
    outfit_top = Column(String, nullable=True)  # e.g., "Green gardening apron"
    outfit_bottom = Column(String, nullable=True)
    helmet_or_hat = Column(String, nullable=True)  # e.g., "Light brown straw hat"
    shoes_or_footwear = Column(String, nullable=True)  # e.g., "Furry paws"
    props = Column(JSON, nullable=True, default=list)  # JSON array: ["Tiny wooden watering can", "woven basket"]
    body_metrics = Column(JSON, nullable=True, default=dict)  # JSON object with height, head, shoulder, etc.
    
    # Scene-specific fields (can vary per scene)
    position = Column(String, nullable=True)  # e.g., "kneeling beside young tomato plants"
    orientation = Column(String, nullable=True)  # e.g., "angled down towards plants"
    pose = Column(String, nullable=True)  # e.g., "kneeling"
    foot_placement = Column(String, nullable=True)  # e.g., "paws tucked under body"
    hand_detail = Column(String, nullable=True)  # e.g., "right paw gently presses soil"
    expression = Column(String, nullable=True)  # e.g., "calm expression"
    action_flow = Column(JSON, nullable=True, default=dict)  # JSON: pre_action, main_action
    
    # Legacy character attributes stored as JSON (for backward compatibility)
    face = Column(JSON, nullable=True, default=dict)
    body = Column(JSON, nullable=True, default=dict)
    clothing = Column(JSON, nullable=True, default=dict)
    personality = Column(JSON, nullable=True, default=dict)
    
    # Consistency seed prompt
    consistency_seed = Column(Text, nullable=True)
    
    # Metadata
    character_metadata = Column("metadata", JSON, nullable=True, default=dict)  # Column name is "metadata" in DB
    
    # Relationships
    project = relationship("Project", backref="characters")
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "age_description": self.age_description or (str(self.age) if self.age else None),
            "species": self.species,
            "voice_personality": self.voice_personality,
            "body_build": self.body_build,
            "face_shape": self.face_shape,
            "hair": self.hair,
            "skin_or_fur_color": self.skin_or_fur_color,
            "signature_feature": self.signature_feature,
            "outfit_top": self.outfit_top,
            "outfit_bottom": self.outfit_bottom,
            "helmet_or_hat": self.helmet_or_hat,
            "shoes_or_footwear": self.shoes_or_footwear,
            "props": self.props or [],
            "body_metrics": self.body_metrics or {},
            "position": self.position,
            "orientation": self.orientation,
            "pose": self.pose,
            "foot_placement": self.foot_placement,
            "hand_detail": self.hand_detail,
            "expression": self.expression,
            "action_flow": self.action_flow or {},
            # Legacy fields
            "face": self.face or {},
            "body": self.body or {},
            "clothing": self.clothing or {},
            "personality": self.personality or {},
            "consistency_seed": self.consistency_seed,
            "metadata": self.character_metadata or {},
        }

