"""
Project database model
"""

from sqlalchemy import Column, String, DateTime, Text, JSON
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
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "script": self.script,
            "metadata": self.project_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

