"""
Project database model
"""

from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.orm import object_session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
from datetime import datetime


class Project(Base):
    """Project model representing a video project"""
    
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    script = Column(Text, nullable=True)
    project_metadata = Column("metadata", JSON, nullable=True, default=dict)  # Column name is "metadata" in DB
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now()
    )
    
    def get_render_settings(self) -> dict:
        """Get render settings with defaults"""
        metadata = self.project_metadata or {}
        render_settings = metadata.get("render_settings", {})
        return {
            "aspect_ratio": render_settings.get("aspect_ratio", "16:9"),
            "videos_per_scene": render_settings.get("videos_per_scene", 2),
            "model": render_settings.get("model", "veo3.1-fast"),
        }
    
    def update_render_settings(self, **kwargs):
        """Update render settings"""
        if not self.project_metadata:
            self.project_metadata = {}
        if "render_settings" not in self.project_metadata:
            self.project_metadata["render_settings"] = {}
        
        if "aspect_ratio" in kwargs:
            self.project_metadata["render_settings"]["aspect_ratio"] = kwargs["aspect_ratio"]
        if "videos_per_scene" in kwargs:
            self.project_metadata["render_settings"]["videos_per_scene"] = kwargs["videos_per_scene"]
        if "model" in kwargs:
            self.project_metadata["render_settings"]["model"] = kwargs["model"]
        
        # Flag the JSON column as modified so SQLAlchemy detects the change
        # This is necessary because SQLAlchemy doesn't detect changes to nested dicts in JSON columns
        try:
            session = object_session(self)
            if session:
                flag_modified(self, "project_metadata")
        except Exception:
            # Object may not be attached to a session yet, which is fine
            pass
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "script": self.script,
            "metadata": self.project_metadata or {},
            "render_settings": self.get_render_settings(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

