#!/usr/bin/env bash
# reboot_recovery.sh - Post-reboot recovery for BraveAutoRelay setup
# Fixes: 1) Firefox stale locks  2) Brave Restore dialog  3) Sets restore_on_startup=1

LOG_PREFIX="[reboot_recovery]"
echo "$LOG_PREFIX Starting post-reboot recovery..."

# 1. Firefox stale lock cleanup
echo "$LOG_PREFIX Checking Firefox lock files..."
FF_FOUND=0
find ~/.mozilla/firefox \( -name "lock" -o -name ".parentlock" \) 2>/dev/null | while read -r f; do
    mv "$f" /tmp/ 2>/dev/null && echo "$LOG_PREFIX  Moved: $f" || echo "$LOG_PREFIX  Could not move: $f"
    FF_FOUND=1
done
[ "$FF_FOUND" -eq 0 ] && echo "$LOG_PREFIX  No Firefox locks - OK" || true

# 2. Brave: patch exit_type + restore_on_startup (only if Brave not running)
echo "$LOG_PREFIX Patching Brave Preferences..."
if pgrep -x "brave" > /dev/null 2>&1; then
    echo "$LOG_PREFIX  Brave already running - skipping patch"
else
    python3 /home/user/Code/BraveAutoRelay/patch_brave_prefs.py
fi

echo "$LOG_PREFIX Done. Launch Brave, then run BraveAutoRelay.py"
