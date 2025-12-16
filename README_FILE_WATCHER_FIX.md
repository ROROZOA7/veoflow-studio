# File Watcher Limit Fix

## Problem
When running development servers (Next.js frontend or FastAPI backend with --reload), you may encounter:
```
ENOSPC: System limit for number of file watchers reached
```

## Solution

### Option 1: Increase System Limit (Recommended - Permanent Fix)

Run the fix script:
```bash
cd /home/duclm/Documents/AI/n8n/text_2_video/veoflow-studio
./fix_file_watcher_limit.sh
```

Or manually:
```bash
# Temporary (current session only)
sudo sysctl fs.inotify.max_user_watches=524288

# Permanent (persists after reboot)
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Option 2: Use Polling Mode (Workaround - No sudo required)

The frontend is already configured to use polling mode, but if issues persist:

1. **Frontend (Next.js)**: Already configured in `package.json` and `next.config.js`
   - Uses `WATCHPACK_POLLING=true` environment variable
   - Uses webpack polling mode

2. **Backend (FastAPI/Uvicorn)**: Already configured in startup scripts
   - Uses `--reload-exclude` flags to exclude large directories

## Verification

Check current limit:
```bash
cat /proc/sys/fs/inotify/max_user_watches
```

Should show `524288` after applying the fix.

## Notes

- Polling mode uses more CPU but avoids file watcher limits
- Increasing the system limit is the preferred solution
- Both solutions can be used together for maximum compatibility



