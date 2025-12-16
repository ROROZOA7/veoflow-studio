#!/bin/bash

# Fix File Watcher Limit for Development
# This increases the system file watcher limit to prevent ENOSPC errors

echo "Fixing file watcher limit..."

# Check current limit
CURRENT_LIMIT=$(cat /proc/sys/fs/inotify/max_user_watches 2>/dev/null || echo "unknown")
echo "Current limit: $CURRENT_LIMIT"

# Increase limit temporarily (for current session)
echo "Increasing limit temporarily to 524288..."
sudo sysctl fs.inotify.max_user_watches=524288

# Make it permanent by adding to sysctl.conf
if ! grep -q "fs.inotify.max_user_watches" /etc/sysctl.conf; then
    echo "Making change permanent..."
    echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
    echo "✓ Limit will persist after reboot"
else
    echo "Limit already configured in /etc/sysctl.conf"
fi

# Verify new limit
NEW_LIMIT=$(cat /proc/sys/fs/inotify/max_user_watches)
echo "New limit: $NEW_LIMIT"
echo ""
echo "✓ File watcher limit fixed!"
echo "You may need to restart your development servers for the change to take full effect."



