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
    age = Column(Integer, nullable=True)
    
    # Character attributes stored as JSON
    face = Column(JSON, nullable=True, default=dict)
    hair = Column(JSON, nullable=True, default=dict)
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
            "face": self.face or {},
            "hair": self.hair or {},
            "body": self.body or {},
            "clothing": self.clothing or {},
            "personality": self.personality or {},
            "consistency_seed": self.consistency_seed,
            "metadata": self.character_metadata or {},
        }

