# Using Your Existing Chrome Profile

## Quick Setup

Run the setup script:

```bash
cd veoflow-studio/backend
./setup_chrome_profile.sh
```

Choose option 2 (copy profile) - this is recommended.

## Manual Setup

### Option 1: Copy Your Chrome Profile

1. **Close Chrome completely:**
   ```bash
   pkill chrome
   ```

2. **Copy your profile:**
   ```bash
   cp -r ~/.config/google-chrome/Default veoflow-studio/backend/chromedata/
   ```

3. **Done!** The automation will use your logged-in session.

### Option 2: Use Profile Directly

Edit `veoflow.config.json`:

```json
{
  "browser": {
    "useExistingProfile": true,
    "existingProfilePath": "/home/duclm/.config/google-chrome/Default"
  }
}
```

**⚠️ Important:** Chrome must be closed when automation runs!

## After Setup

1. **Restart Celery worker** to pick up changes
2. **Try rendering a scene** - it should use your logged-in session
3. **Check browser window** - you should already be logged in

## Troubleshooting

- **"Target closed" error:** Close Chrome and try again
- **"No elements found":** The page may need more time to load - wait and retry
- **Login still required:** Make sure you copied the profile correctly
