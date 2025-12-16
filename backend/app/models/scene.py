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
    prompt = Column(Text, nullable=False)  # Detailed prompt for video generation
    script = Column(Text, nullable=True)  # Scene script text
    
    # New detailed fields
    scene_description = Column(Text, nullable=True)  # Brief description of the scene
    duration_sec = Column(Integer, nullable=True)  # Scene duration in seconds
    visual_style = Column(Text, nullable=True)  # e.g., "High-quality 3D animation in Pixar's signature style"
    environment = Column(Text, nullable=True)  # e.g., "Garden with young tomato plants, soft morning light"
    camera_angle = Column(String, nullable=True)  # e.g., "Medium shot, slightly angled down"
    character_adaptations = Column(JSON, nullable=True, default=dict)  # Scene-specific character details
    
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
            "scene_description": self.scene_description,
            "duration_sec": self.duration_sec,
            "visual_style": self.visual_style,
            "environment": self.environment,
            "camera_angle": self.camera_angle,
            "character_adaptations": self.character_adaptations or {},
            "video_path": self.video_path,
            "thumbnail_path": self.thumbnail_path,
            "metadata": self.scene_metadata or {},
            "status": self.status,
        }

