"""
Script database model
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
from datetime import datetime


class Script(Base):
    """Script model representing a generated video script"""
    
    __tablename__ = "scripts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, unique=True)
    
    # User input parameters (required)
    main_content = Column(Text, nullable=False)
    video_duration = Column(Integer, nullable=False)  # Total duration in seconds
    style = Column(String, nullable=False)  # e.g., "cartoon", "3D animation", "realistic"
    target_audience = Column(String, nullable=False)  # e.g., "children", "adults", "teenagers"
    aspect_ratio = Column(String, nullable=False)  # e.g., "16:9", "9:16", "1:1", "4:3"
    
    # Optional parameters
    language = Column(String, nullable=True)  # e.g., "en-US", "vi-VN"
    voice_style = Column(String, nullable=True)  # e.g., "narrator", "character voices"
    music_style = Column(String, nullable=True)  # e.g., "upbeat", "calm", "dramatic"
    color_palette = Column(String, nullable=True)  # e.g., "bright", "muted", "pastel"
    transition_style = Column(String, nullable=True)  # e.g., "smooth", "cut", "fade"
    
    # Generated content
    full_script = Column(Text, nullable=True)  # Complete script text
    story_structure = Column(JSON, nullable=True)  # JSON: beginning, middle, end
    scene_count = Column(Integer, nullable=True)  # Calculated number of scenes
    generated_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    
    # Relationships
    project = relationship("Project", backref="scripts")
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "main_content": self.main_content,
            "video_duration": self.video_duration,
            "style": self.style,
            "target_audience": self.target_audience,
            "aspect_ratio": self.aspect_ratio,
            "language": self.language,
            "voice_style": self.voice_style,
            "music_style": self.music_style,
            "color_palette": self.color_palette,
            "transition_style": self.transition_style,
            "full_script": self.full_script,
            "story_structure": self.story_structure or {},
            "scene_count": self.scene_count,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }

