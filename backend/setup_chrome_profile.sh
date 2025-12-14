#!/bin/bash
# Helper script to set up Chrome profile for VeoFlow Studio

echo "=========================================="
echo "VeoFlow Studio - Chrome Profile Setup"
echo "=========================================="
echo ""

# Find Chrome profile
CHROME_PROFILE=""
if [ -d "$HOME/.config/google-chrome/Default" ]; then
    CHROME_PROFILE="$HOME/.config/google-chrome/Default"
    echo "✓ Found Chrome profile: $CHROME_PROFILE"
elif [ -d "$HOME/.config/chromium/Default" ]; then
    CHROME_PROFILE="$HOME/.config/chromium/Default"
    echo "✓ Found Chromium profile: $CHROME_PROFILE"
else
    echo "✗ Could not find Chrome/Chromium profile"
    echo "  Please provide the path manually"
    exit 1
fi

echo ""
echo "Choose an option:"
echo "1. Use existing profile directly (Chrome must be closed)"
echo "2. Copy profile to automation directory (recommended)"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "Updating veoflow.config.json to use existing profile..."
        python3 << PYEOF
import json
config_path = "veoflow.config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

config['browser']['useExistingProfile'] = True
config['browser']['existingProfilePath'] = "$CHROME_PROFILE"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Config updated!")
print("⚠️  IMPORTANT: Close Chrome before running automation!")
PYEOF
        echo ""
        echo "✓ Setup complete!"
        echo "⚠️  Remember to close Chrome before running automation"
        ;;
    2)
        echo ""
        echo "Copying Chrome profile..."
        
        # Check if Chrome is running
        if pgrep -x "chrome" > /dev/null || pgrep -x "chromium" > /dev/null || pgrep -f "google-chrome" > /dev/null; then
            echo "⚠️  Chrome/Chromium is currently running!"
            echo "   Please close Chrome completely before copying the profile."
            echo ""
            read -p "   Press Enter after closing Chrome, or Ctrl+C to cancel..."
            
            # Wait a bit more and check again
            sleep 1
            if pgrep -x "chrome" > /dev/null || pgrep -x "chromium" > /dev/null || pgrep -f "google-chrome" > /dev/null; then
                echo "❌ Chrome is still running. Please close it and try again."
                exit 1
            fi
        fi
        
        # Copy profile
        TARGET_DIR="./chromedata"
        
        # Remove old directory if it exists
        if [ -d "$TARGET_DIR" ]; then
            echo "Removing old profile copy..."
            rm -rf "$TARGET_DIR"
        fi
        
        mkdir -p "$TARGET_DIR"
        
        echo "Copying files (this may take 1-2 minutes)..."
        echo "   Source: $CHROME_PROFILE"
        echo "   Target: $TARGET_DIR"
        echo ""
        
        # Use rsync if available (better for large directories), otherwise use cp
        if command -v rsync > /dev/null 2>&1; then
            echo "Using rsync for faster copying..."
            rsync -a --progress "$CHROME_PROFILE/" "$TARGET_DIR/" 2>&1 | head -20
            COPY_RESULT=$?
        else
            echo "Using cp (this may take longer)..."
            cp -r "$CHROME_PROFILE"/* "$TARGET_DIR/" 2>&1
            COPY_RESULT=$?
        fi
        
        if [ $COPY_RESULT -eq 0 ]; then
            # Verify some key files were copied
            if [ -f "$TARGET_DIR/Cookies" ] || [ -d "$TARGET_DIR/Default" ] || [ -f "$TARGET_DIR/Preferences" ]; then
                echo ""
                echo "✓ Profile copied successfully to $TARGET_DIR"
                
                # Update config
                python3 << PYEOF
import json
import os
config_path = "veoflow.config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

config['browser']['useExistingProfile'] = False
config['browser']['chromeProfilePath'] = "./chromedata"
config['browser']['userDataDir'] = "./chromedata"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✓ Config updated to use copied profile")
PYEOF
                echo ""
                echo "✓ Setup complete! You can now open Chrome normally."
            else
                echo ""
                echo "⚠️  Warning: Profile copy may be incomplete. Some files may be missing."
                echo "   This might still work, but you may need to log in again."
            fi
        else
            echo ""
            echo "❌ Error: Failed to copy profile. Error code: $COPY_RESULT"
            echo "   Possible causes:"
            echo "   - Chrome is still running (close it completely)"
            echo "   - Permission issues (check file permissions)"
            echo "   - Disk space (check available space)"
            exit 1
        fi
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Next steps:"
echo "1. Make sure you're logged into Google Flow in Chrome"
echo "2. Restart Celery worker to pick up changes"
echo "3. Try rendering a scene"

