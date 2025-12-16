# Test Render All Scenes - Execution Guide

## Fixes Implemented

All fixes have been implemented in:
- `app/services/flow_controller.py` - Fixed `ensure_new_project` to navigate to gallery when `force_new=True`
- `app/services/render_manager.py` - Added scene context logging

## How to Run the Test

### Prerequisites

1. **Backend server must be running** (with latest code):
```bash
cd /home/duclm/Documents/AI/n8n/text_2_video/veoflow-studio/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. **Celery worker must be running** (with latest code):
```bash
cd /home/duclm/Documents/AI/n8n/text_2_video/veoflow-studio/backend
source venv/bin/activate
celery -A app.workers.render_worker worker --loglevel=info
```

3. **Redis must be running** (for Celery):
```bash
redis-server
```

### Run the Test

```bash
cd /home/duclm/Documents/AI/n8n/text_2_video/veoflow-studio/backend
source venv/bin/activate

# Test with specific project
python3 test_render_all_scenes.py --project-id test-project-001

# Or let it find first project with pending scenes
python3 test_render_all_scenes.py
```

## What the Test Does

1. **Finds a project** with pending scenes (or uses specified project)
2. **Resets scene statuses** to "pending" if needed
3. **Queues render tasks** for all pending scenes (matching API behavior)
4. **Monitors execution** by checking Celery task status every 5 seconds
5. **Reports results** showing which scenes succeeded/failed

## Expected Behavior (After Fixes)

### Scene 1:
- Should navigate to gallery (if already in editor)
- Should click "New project" button
- Should inject prompt successfully
- Should trigger generation
- Logs should show: `[Scene 1 ID: ...]` prefix

### Scene 2:
- Should navigate to gallery (getting fresh editor)
- Should click "New project" button
- Should inject its own prompt (not Scene 1's)
- Should trigger generation only once
- Logs should show: `[Scene 2 ID: ...]` prefix

## Checking Logs

### Backend Logs (veoflow.log):
```bash
tail -f logs/veoflow.log | grep -E "Scene [12]|ensure_new_project|inject_prompt"
```

### Celery Worker Logs (stdout/stderr):
Check the terminal where you ran the Celery worker - logs should show:
- `=== RENDER TASK STARTED ===`
- `[Scene 1 ID: ...]` or `[Scene 2 ID: ...]` messages
- `[ensure_new_project]` navigation messages
- Prompt injection confirmations

### Test Script Output:
The test script will show:
- Task queuing status
- Real-time task execution status
- Final summary with success/failure counts

## Troubleshooting

### If Scene 1 doesn't send:
1. Check Celery worker logs for errors
2. Look for `[Scene 1 ID: ...]` messages in logs
3. Check if `ensure_new_project` is navigating to gallery
4. Verify browser profile is accessible

### If Scene 2 sends twice:
1. Check logs for duplicate `inject_prompt` calls
2. Verify each scene gets a fresh editor (check `ensure_new_project` logs)
3. Look for `[Scene 2 ID: ...]` messages to track execution

### If tasks don't execute:
1. Check Celery worker is running: `ps aux | grep celery`
2. Check Redis is running: `redis-cli ping`
3. Check worker can connect to Redis
4. Check for errors in Celery worker stdout/stderr

## Test Status

✅ Test script created: `test_render_all_scenes.py`
✅ Fixes implemented in code
✅ Test can queue tasks successfully

**Next Steps:**
1. Ensure backend and Celery worker are restarted with latest code
2. Run the test and monitor logs
3. Verify Scene 1 sends properly
4. Verify Scene 2 sends only once
5. Check final scene statuses in database


