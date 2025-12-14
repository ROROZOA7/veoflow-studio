"""
Scene database model
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Scene(Base):
    """Scene model representing a single scene in a project"""
    
    __tablename__ = "scenes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    number = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    script = Column(Text, nullable=True)
    video_path = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    scene_metadata = Column("metadata", JSON, nullable=True, default=dict)  # Column name is "metadata" in DB
    status = Column(String, default="pending")  # pending, rendering, completed, failed
    
    # Relationships
    project = relationship("Project", backref="scenes")
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "number": self.number,
            "prompt": self.prompt,
            "script": self.script,
            "video_path": self.video_path,
            "thumbnail_path": self.thumbnail_path,
            "metadata": self.scene_metadata or {},
            "status": self.status,
        }

