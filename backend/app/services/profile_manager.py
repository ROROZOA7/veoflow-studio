"""
Profile Manager Service - Manages Chrome profiles
"""

import logging
import uuid
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.core.database import SessionLocal
from app.config import config_manager, settings

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manages Chrome profile creation, deletion, and selection"""
    
    def __init__(self):
        self.profiles_dir = Path(config_manager.get("profiles.directory", "./profiles"))
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def create_profile(self, name: str) -> Profile:
        """Create a new Chrome profile"""
        db = SessionLocal()
        try:
            # Check if name already exists
            existing = db.query(Profile).filter(Profile.name == name).first()
            if existing:
                raise ValueError(f"Profile with name '{name}' already exists")
            
            # Generate profile ID and path
            profile_id = str(uuid.uuid4())
            profile_path = self.profiles_dir / f"profile-{profile_id}"
            profile_path.mkdir(parents=True, exist_ok=True)
            
            # Create Default subdirectory for Chrome
            default_dir = profile_path / "Default"
            default_dir.mkdir(exist_ok=True)
            
            # Create profile in database
            profile = Profile(
                id=profile_id,
                name=name,
                profile_path=str(profile_path.absolute()),
                is_active=False,
                metadata={}
            )
            
            db.add(profile)
            db.commit()
            db.refresh(profile)
            
            logger.info(f"Created profile: {name} at {profile_path}")
            return profile
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create profile: {e}")
            raise
        finally:
            db.close()
    
    def list_profiles(self) -> List[Profile]:
        """List all profiles"""
        db = SessionLocal()
        try:
            profiles = db.query(Profile).order_by(Profile.created_at.desc()).all()
            return profiles
        finally:
            db.close()
    
    def get_profile(self, profile_id: str) -> Optional[Profile]:
        """Get profile by ID"""
        db = SessionLocal()
        try:
            return db.query(Profile).filter(Profile.id == profile_id).first()
        finally:
            db.close()
    
    def get_profile_by_name(self, name: str) -> Optional[Profile]:
        """Get profile by name"""
        db = SessionLocal()
        try:
            return db.query(Profile).filter(Profile.name == name).first()
        finally:
            db.close()
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete profile and its directory"""
        db = SessionLocal()
        try:
            profile = db.query(Profile).filter(Profile.id == profile_id).first()
            if not profile:
                raise ValueError(f"Profile {profile_id} not found")
            
            # Delete directory
            profile_path = Path(profile.profile_path)
            if profile_path.exists():
                import shutil
                shutil.rmtree(profile_path)
                logger.info(f"Deleted profile directory: {profile_path}")
            
            # Delete from database
            db.delete(profile)
            db.commit()
            
            logger.info(f"Deleted profile: {profile.name}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete profile: {e}")
            raise
        finally:
            db.close()
    
    def set_active_profile(self, profile_id: str) -> None:
        """Set profile as active (only one can be active)"""
        db = SessionLocal()
        try:
            # Deactivate all profiles
            db.query(Profile).update({"is_active": False})
            
            # Activate specified profile
            profile = db.query(Profile).filter(Profile.id == profile_id).first()
            if not profile:
                raise ValueError(f"Profile {profile_id} not found")
            
            profile.is_active = True
            db.commit()
            
            # Update config
            config_manager.set("profiles.activeProfileId", profile_id)
            
            logger.info(f"Set active profile: {profile.name}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to set active profile: {e}")
            raise
        finally:
            db.close()
    
    def get_active_profile(self) -> Optional[Profile]:
        """Get the currently active profile"""
        db = SessionLocal()
        try:
            return db.query(Profile).filter(Profile.is_active == True).first()
        finally:
            db.close()
    
    def get_profile_path(self, profile_id: str) -> Path:
        """Get profile directory path"""
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")
        return Path(profile.profile_path)
    
    def get_active_profile_path(self) -> Optional[Path]:
        """Get active profile path, or default if none"""
        active = self.get_active_profile()
        if active:
            return Path(active.profile_path)
        
        # Fallback to default from config
        default_path = Path(config_manager.get(
            "browser.chromeProfilePath",
            settings.CHROME_PROFILE_PATH
        ))
        return default_path if default_path.exists() else None

