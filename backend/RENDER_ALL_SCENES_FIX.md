# Render All Scenes - Issues and Fixes

## Issues Detected from Logs (project: test-project-001)

### Issue 1: Scene 1 Not Sending Prompt
**Root Cause:**
- When `force_new=True` is used (for automated scene rendering), the code detected that we're already in an editor view
- However, it only tried to find the "New project" button, which doesn't exist when already in editor view
- Result: Scene 1 tried to inject prompt into a stale editor or failed silently before sending

### Issue 2: Scene 2 Sending Twice
**Root Cause:**
- Scene 2 reused the same editor from Scene 1 (or a stale state)
- Because `ensure_new_project` with `force_new=True` didn't actually navigate to gallery first when in editor view, Scene 2 got the same editor with leftover state
- This caused Scene 2's prompt to be injected multiple times or trigger generation twice

### Issue 3: Missing Execution Logs
**Observation:**
- Tasks were queued successfully (seen in logs at 23:29:37)
- But no execution logs appeared in the log files
- Celery worker is running, but logs might be going to stdout/stderr instead of log files

## Fixes Applied

### Fix 1: Navigate to Gallery When force_new=True
**File:** `app/services/flow_controller.py`

**Changes:**
- When `force_new=True` and we're already in an editor view, now we:
  1. Try to find and click "Home" or "Gallery" button to navigate to gallery view
  2. If that fails, navigate directly to Flow URL to get gallery view
  3. Wait for gallery to load before trying to click "New project"

**Code location:** Lines ~1026-1057

### Fix 2: Enhanced Logging
**Files:** `app/services/render_manager.py`, `app/services/flow_controller.py`

**Changes:**
- Added scene context to all log messages: `[Scene {number} ID: {id}]`
- Added logging at each step:
  - Before ensuring new project
  - After editor is ready
  - Before/after prompt injection
  - Before/after triggering generation
  - Generation trigger results

**Benefits:**
- Easier to trace which scene is doing what
- Can identify if Scene 1 or Scene 2 is failing
- Can see if prompts are being sent multiple times

### Fix 3: Better Error Handling
**Changes:**
- Added try/catch around gallery navigation with fallback
- Better error messages explaining what's happening

## How to Test

1. **Restart backend and Celery worker** to pick up changes:
```bash
cd /home/duclm/Documents/AI/n8n/text_2_video/veoflow-studio/backend
# Restart backend (if using uvicorn with --reload, it should auto-reload)
# Restart Celery worker
celery -A app.workers.render_worker worker --loglevel=info
```

2. **Run "Render All Scenes"** for a project with multiple scenes

3. **Check logs** for:
   - `[Scene 1 ID: ...]` and `[Scene 2 ID: ...]` prefixes
   - `[ensure_new_project]` messages showing navigation to gallery
   - Prompt injection messages with scene context
   - Generation trigger results

4. **Verify in Flow UI:**
   - Scene 1 should send its prompt and generate video
   - Scene 2 should send its prompt (only once) and generate video
   - Each scene should use a fresh Flow project/editor

## Expected Log Flow

```
[Scene 1 ID: xxx] Ensuring we're in editor view (force_new=True...)
[ensure_new_project] Checking if we need to create a new project (force_new=True)...
[ensure_new_project] Already in editor view, but force_new=True - navigating to gallery...
[Scene 1 ID: xxx] ✓ Editor view ready for prompt injection
[Scene 1 ID: xxx] Injecting prompt into Flow editor...
[Scene 1 ID: xxx] ✓ Prompt injected
[Scene 1 ID: xxx] Triggering video generation...
[Scene 1 ID: xxx] Generation trigger result: True

[Scene 2 ID: yyy] Ensuring we're in editor view (force_new=True...)
[ensure_new_project] Checking if we need to create a new project (force_new=True)...
[ensure_new_project] Already in editor view, but force_new=True - navigating to gallery...
[Scene 2 ID: yyy] ✓ Editor view ready for prompt injection
[Scene 2 ID: yyy] Injecting prompt into Flow editor...
[Scene 2 ID: yyy] ✓ Prompt injected
[Scene 2 ID: yyy] Triggering video generation...
[Scene 2 ID: yyy] Generation trigger result: True
```

## Notes

- Each scene now gets a truly fresh editor by navigating to gallery and clicking "New project"
- Scene context in logs makes it easy to debug which scene is having issues
- If you still see issues, check the Celery worker stdout/stderr (where the worker is running) as logs might not be going to log files


