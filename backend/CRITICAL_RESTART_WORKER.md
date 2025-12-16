# ⚠️ CRITICAL: Restart Celery Worker NOW

## Problem Identified

**Scene 1 status: FAILED** - The prompt "a lion walking" was never sent to Flow
**Scene 2 status: COMPLETED** - But appears twice in Flow (sent multiple times)

## Root Cause

The Celery worker running from 21:48 has the **OLD CODE** without our fixes. There are TWO workers running, and tasks are being picked up by the old worker.

## Action Required

**YOU MUST RESTART THE CELERY WORKER** to apply the fixes:

1. **Find and kill ALL Celery workers:**
```bash
# Find all celery workers
ps aux | grep "celery.*render_worker" | grep -v grep

# Kill all of them (use the PIDs from above)
kill <PID1> <PID2> <PID3> ...

# OR kill all at once
pkill -f "celery.*render_worker"
```

2. **Start a fresh worker with the NEW code:**
```bash
cd /home/duclm/Documents/AI/n8n/text_2_video/veoflow-studio/backend
source venv/bin/activate
celery -A app.workers.render_worker worker --loglevel=info
```

3. **Verify the new code is loaded** by looking for these log messages when tasks run:
   - `[Scene X ID: ...] ===== RENDER SCENE STARTED =====`
   - `[Scene X ID: ...] Navigating to Flow...`
   - `[ensure_new_project] Already in editor view, but force_new=True - navigating to gallery...`

## What the Fixes Do

1. **Scene 1 will now work**: Each scene navigates to gallery first, then clicks "New project" to get a fresh editor
2. **Scene 2 won't send twice**: Each scene gets its own fresh editor, preventing state reuse
3. **Better logging**: You'll see `[Scene X ID: ...]` in all logs to track which scene is doing what

## After Restarting

1. Reset scene statuses to pending:
```bash
cd /home/duclm/Documents/AI/n8n/text_2_video/veoflow-studio/backend
source venv/bin/activate
python3 -c "from app.core.database import SessionLocal; from app.models.scene import Scene; db = SessionLocal(); [setattr(s, 'status', 'pending') or db.commit() for s in db.query(Scene).filter(Scene.project_id == 'test-project-001').all()]; print('Reset scenes to pending'); db.close()"
```

2. Run test again:
```bash
python3 test_render_all_scenes.py --project-id test-project-001
```

3. Monitor logs - you should now see Scene 1 executing properly with the new logging!


