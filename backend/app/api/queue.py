"""
Queue API endpoints
"""

from fastapi import APIRouter
from celery import current_app
from app.workers.render_worker import celery_app

router = APIRouter()


@router.get("")
async def list_queue():
    """List active tasks in queue"""
    inspect = current_app.control.inspect()
    
    active = inspect.active() or {}
    scheduled = inspect.scheduled() or {}
    reserved = inspect.reserved() or {}
    
    tasks = []
    
    # Combine all task types
    for worker, task_list in active.items():
        for task in task_list:
            tasks.append({
                "task_id": task["id"],
                "name": task["name"],
                "worker": worker,
                "status": "active"
            })
    
    for worker, task_list in scheduled.items():
        for task in task_list:
            tasks.append({
                "task_id": task["request"]["id"],
                "name": task["request"]["task"],
                "worker": worker,
                "status": "scheduled"
            })
    
    return {"tasks": tasks}


@router.get("/stats")
async def queue_stats():
    """Get queue statistics"""
    inspect = current_app.control.inspect()
    
    active = inspect.active() or {}
    scheduled = inspect.scheduled() or {}
    reserved = inspect.reserved() or {}
    
    stats = {
        "active": sum(len(tasks) for tasks in active.values()),
        "scheduled": sum(len(tasks) for tasks in scheduled.values()),
        "reserved": sum(len(tasks) for tasks in reserved.values()),
        "workers": len(active.keys())
    }
    
    return stats

