#!/usr/bin/env bash
LOG_PREFIX="[reboot_recovery]"
echo "$LOG_PREFIX Starting..."

find ~/snap/firefox/common/.mozilla/firefox -name "lock" -o -name ".parentlock" 2>/dev/null | while read -r f; do
    mv "$f" /tmp/ 2>/dev/null && echo "$LOG_PREFIX Cleared snap lock: $f"
done

find ~/.mozilla/firefox \( -name "lock" -o -name ".parentlock" \) 2>/dev/null | while read -r f; do
    mv "$f" /tmp/ 2>/dev/null && echo "$LOG_PREFIX Cleared legacy lock: $f"
done

if pgrep -x "brave" > /dev/null 2>&1; then
    echo "$LOG_PREFIX Brave already running - skipping patch"
else
    python3 /home/user/Code/BraveAutoRelay/patch_brave_prefs.py
fi

echo "$LOG_PREFIX Done."
