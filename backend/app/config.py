"""
Application configuration management
"""

import json
import os
from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./veoflow.db",
        description="Database connection URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for Celery"
    )
    
    # API
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000",
        description="CORS allowed origins (comma-separated)"
    )
    
    # AI Services
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key")
    GEMINI_API_KEY: str = Field(default="", description="Gemini API key")
    
    # Browser
    BROWSER_HEADLESS: bool = Field(default=False, description="Run browser in headless mode")
    CHROME_PROFILE_PATH: str = Field(
        default="./chromedata",
        description="Chrome profile path"
    )
    
    # Profiles
    PROFILES_DIRECTORY: str = Field(
        default="./profiles",
        description="Directory for storing Chrome profiles"
    )
    ACTIVE_PROFILE_ID: str = Field(
        default="",
        description="ID of the active profile"
    )
    
    # Flow
    FLOW_URL: str = Field(
        default="https://labs.google/fx/tools/flow/",
        description="Google Flow URL"
    )
    
    # Paths
    DOWNLOADS_PATH: str = Field(default="./output", description="Downloads directory")
    PROJECTS_PATH: str = Field(default="./projects", description="Projects directory")
    TEMP_PATH: str = Field(default="./temp", description="Temporary files directory")
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for encryption"
    )
    ENCRYPT_COOKIES: bool = Field(default=True, description="Encrypt stored cookies")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class ConfigManager:
    """Manages veoflow.config.json configuration file"""
    
    def __init__(self, config_path: str = "veoflow.config.json"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from JSON file"""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        else:
            # Default configuration
            self.config = self._default_config()
            self.save_config()
    
    def save_config(self) -> None:
        """Save configuration to JSON file"""
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-separated key"""
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "browser": {
                "engine": "playwright",
                "headless": False,
                "chromeProfilePath": "./chromedata",
                "userDataDir": "./chromedata",
                "useExistingProfile": False,
                "existingProfilePath": "",
                "viewport": {"width": 1920, "height": 1080},
                "slowMo": 100,
                "timeout": 60000
            },
            "flow": {
                "url": "https://labs.google/fx/tools/flow/project/",
                "timeoutGenerateMs": 240000,
                "pollingIntervalMs": 2000,
                "maxRetries": 3,
                "retryDelayMs": 5000,
                "selectors": {
                    "promptInput": "textarea[placeholder*='prompt'], textarea[aria-label*='prompt']",
                    "generateButton": "button:has-text('Generate'), button[aria-label*='Generate']",
                    "videoElement": "video",
                    "downloadButton": "button:has-text('Download'), a[download]",
                    "errorMessage": ".error, [role='alert']"
                }
            },
            "paths": {
                "downloads": "./output",
                "projects": "./projects",
                "chromedata": "./chromedata",
                "temp": "./temp"
            },
            "render": {
                "videoFormat": "mp4",
                "stitchUsingFFmpeg": True,
                "defaultTransition": "fade",
                "transitionDuration": 0.5,
                "outputResolution": "1920x1080",
                "fps": 30
            },
            "ai": {
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "apiKey": "",
                "temperature": 0.7,
                "maxTokens": 2000
            },
            "queue": {
                "concurrency": 1,
                "maxAttempts": 3,
                "backoff": {"type": "exponential", "delay": 5000}
            },
            "security": {
                "encryptCookies": True,
                "cookieExpiryDays": 30,
                "rateLimit": {
                    "enabled": True,
                    "maxRequests": 10,
                    "windowMs": 60000
                }
            },
            "profiles": {
                "directory": "./profiles",
                "activeProfileId": None
            }
        }


# Global instances
settings = Settings()
config_manager = ConfigManager()

# Convenience accessors
FLOW_URL = config_manager.get("flow.url", settings.FLOW_URL)
FLOW_SELECTORS = config_manager.get("flow.selectors", {})
BROWSER_HEADLESS = config_manager.get("browser.headless", settings.BROWSER_HEADLESS)
CHROME_PROFILE_PATH = config_manager.get("browser.chromeProfilePath", settings.CHROME_PROFILE_PATH)
DOWNLOADS_PATH = config_manager.get("paths.downloads", settings.DOWNLOADS_PATH)
POLLING_INTERVAL_MS = config_manager.get("flow.pollingIntervalMs", 2000)

