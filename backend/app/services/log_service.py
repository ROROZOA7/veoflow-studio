"""
Centralized Logging Service - Captures and stores all application logs
"""

import logging
import json
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from collections import deque
from threading import Lock

logger = logging.getLogger(__name__)


class LogService:
    """Centralized logging service that stores logs in memory and file"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # In-memory log buffer (last 1000 entries)
        self.log_buffer: deque = deque(maxlen=1000)
        self.buffer_lock = Lock()
        
        # Log file
        self.log_file = self.logs_dir / "veoflow_app.log"
        
        # Setup custom handler
        self.setup_handler()
        
        self._initialized = True
    
    def setup_handler(self):
        """Setup custom logging handler"""
        handler = LogHandler(self)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
    
    def add_log(self, level: str, logger_name: str, message: str, extra: Optional[Dict] = None):
        """Add a log entry"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": logger_name,
            "message": message,
            "extra": extra or {}
        }
        
        # Add to buffer
        with self.buffer_lock:
            self.log_buffer.append(log_entry)
        
        # Write to file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            # Fallback to stderr if file write fails
            print(f"Failed to write log: {e}", file=sys.stderr)
    
    def get_logs(
        self,
        level: Optional[str] = None,
        logger_name: Optional[str] = None,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Dict]:
        """Get logs from buffer"""
        with self.buffer_lock:
            logs = list(self.log_buffer)
        
        # Filter
        if level:
            logs = [log for log in logs if log["level"] == level.upper()]
        if logger_name:
            logs = [log for log in logs if logger_name.lower() in log["logger"].lower()]
        if since:
            since_iso = since.isoformat()
            logs = [log for log in logs if log["timestamp"] >= since_iso]
        
        # Return most recent first, limit
        return list(reversed(logs[-limit:]))
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Get most recent logs"""
        return self.get_logs(limit=limit)
    
    def clear_logs(self):
        """Clear log buffer"""
        with self.buffer_lock:
            self.log_buffer.clear()
    
    def get_log_file_path(self) -> Path:
        """Get path to log file"""
        return self.log_file


class LogHandler(logging.Handler):
    """Custom logging handler that sends logs to LogService"""
    
    def __init__(self, log_service: LogService):
        super().__init__()
        self.log_service = log_service
    
    def emit(self, record):
        """Emit a log record"""
        try:
            level = record.levelname
            logger_name = record.name
            message = self.format(record)
            
            # Extract extra fields
            extra = {}
            if hasattr(record, 'task_id'):
                extra['task_id'] = record.task_id
            if hasattr(record, 'scene_id'):
                extra['scene_id'] = record.scene_id
            if hasattr(record, 'project_id'):
                extra['project_id'] = record.project_id
            if hasattr(record, 'profile_id'):
                extra['profile_id'] = record.profile_id
            
            self.log_service.add_log(level, logger_name, message, extra)
        except Exception:
            # Don't let logging errors break the application
            pass


# Global instance
log_service = LogService()

