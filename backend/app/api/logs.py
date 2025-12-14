"""
Logs API endpoints - Expose application logs for debugging
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime
from app.services.log_service import log_service
from pydantic import BaseModel

router = APIRouter()


class LogEntry(BaseModel):
    timestamp: str
    level: str
    logger: str
    message: str
    extra: dict


class LogsResponse(BaseModel):
    logs: List[LogEntry]
    total: int
    has_more: bool


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    logger_name: Optional[str] = Query(None, description="Filter by logger name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    since: Optional[str] = Query(None, description="ISO timestamp to get logs since")
):
    """Get application logs"""
    try:
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid 'since' timestamp format. Use ISO format.")
        
        logs = log_service.get_logs(
            level=level,
            logger_name=logger_name,
            limit=limit,
            since=since_dt
        )
        
        return {
            "logs": logs,
            "total": len(logs),
            "has_more": len(logs) >= limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.get("/logs/recent", response_model=LogsResponse)
async def get_recent_logs(limit: int = Query(100, ge=1, le=1000)):
    """Get most recent logs"""
    try:
        logs = log_service.get_recent_logs(limit=limit)
        return {
            "logs": logs,
            "total": len(logs),
            "has_more": len(logs) >= limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent logs: {str(e)}")


@router.delete("/logs")
async def clear_logs():
    """Clear log buffer"""
    try:
        log_service.clear_logs()
        return {"message": "Logs cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {str(e)}")


@router.get("/logs/file")
async def get_log_file_path():
    """Get path to log file"""
    try:
        return {
            "path": str(log_service.get_log_file_path().absolute()),
            "exists": log_service.get_log_file_path().exists()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log file path: {str(e)}")

