#!/usr/bin/env python3
"""
BraveAutoRelay.py - Automated OpenClaw Browser Relay Tab Checker
Monitors browser tabs and activates disabled relay badges.

Usage:
  python3 BraveAutoRelay.py              # Normal run
  python3 BraveAutoRelay.py --calibrate  # Calibration mode (capture reference images)
  python3 BraveAutoRelay.py --snapshot   # Just take a top-300px snapshot and send to Discord
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import pyautogui
import requests

# ── Configuration ────────────────────────────────────────────────────────────
REPO_DIR        = Path(__file__).parent
IMAGES_DIR      = REPO_DIR / "images"
ENV_FILE        = REPO_DIR / ".env"
DISCORD_CHANNEL = "1470284617151152261"   # #logs
TEMP_SHOT       = REPO_DIR / "temp_screenshot.png"

RELAY_DISABLED  = IMAGES_DIR / "relay_disabled.png"
RELAY_ENABLED   = IMAGES_DIR / "relay_enabled.png"
TAB_CLOSE       = IMAGES_DIR / "tab_close.png"

load_dotenv(ENV_FILE)
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.15


# ── Helpers ──────────────────────────────────────────────────────────────────

def top_region():
    """Return (0, 0, screen_w, 300) for top-300px operations."""
    w, h = pyautogui.size()
    return (0, 0, w, min(300, h))


def snapshot(region=None) -> Path | None:
    """Screenshot → TEMP_SHOT. Returns path or None on failure."""
    try:
        reg = region or top_region()
        img = pyautogui.screenshot(region=reg)
        img.save(TEMP_SHOT)
        return TEMP_SHOT
    except Exception as e:
        print(f"[snapshot] failed: {e}", file=sys.stderr)
        return None


def discord_send(message: str, image_path: Path | None = None):
    """Post message (+ optional image) to Discord #logs."""
    if not DISCORD_TOKEN:
        print(f"[discord] no token — skipping send: {message}")
        return
    url     = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL}/messages"
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    try:
        if image_path and image_path.exists():
            with open(image_path, "rb") as f:
                r = requests.post(url, headers=headers,
                                  data={"content": message},
                                  files={"file": ("screenshot.png", f, "image/png")},
                                  timeout=10)
        else:
            r = requests.post(url, headers=headers,
                              json={"content": message}, timeout=10)
        if r.status_code not in (200, 201, 204):
            print(f"[discord] HTTP {r.status_code}: {r.text}", file=sys.stderr)
    except Exception as e:
        print(f"[discord] send failed: {e}", file=sys.stderr)


def find(img_path: Path, region=None, confidence=0.8):
    """Locate img_path on screen. Returns Box or None."""
    if not img_path.exists():
        return None
    try:
        return pyautogui.locateOnScreen(str(img_path),
                                        confidence=confidence,
                                        region=region or top_region())
    except Exception:
        return None


def images_ready() -> bool:
    return all(p.exists() for p in (RELAY_DISABLED, RELAY_ENABLED, TAB_CLOSE))


# ── Modes ────────────────────────────────────────────────────────────────────

def snapshot_mode():
    """Take a top-300px screenshot, send to Discord, exit."""
    print("[snapshot-mode] taking screenshot...")
    path = snapshot()
    msg  = ("📸 BraveAutoRelay — snapshot of top 300px.\n"
            "Save reference images to:\n"
            f"`{IMAGES_DIR}/relay_disabled.png`\n"
            f"`{IMAGES_DIR}/relay_enabled.png`\n"
            f"`{IMAGES_DIR}/tab_close.png`\n"
            "Then re-run without `--snapshot`.")
    discord_send(msg, path)
    print("[snapshot-mode] done — screenshot sent to Discord #logs.")
    sys.exit(0)


def calibrate_mode():
    """Interactive calibration: user positions target, presses Enter, script crops."""
    print("\n📸 CALIBRATION MODE\n")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    steps = [
        (RELAY_DISABLED, "Hover over the DISABLED OpenClaw relay icon in the Brave toolbar"),
        (RELAY_ENABLED,  "Hover over the ENABLED/ON relay badge in the Brave toolbar"),
        (TAB_CLOSE,      "Hover over the X (close) button of any tab"),
    ]
    for path, hint in steps:
        print(f"\n▶  {hint}")
        input("   Press Enter to take screenshot…")
        shot = snapshot()
        if shot:
            import shutil
            shutil.copy(shot, path)
            print(f"   ✅ Saved {path.name}")
        else:
            print(f"   ❌ Screenshot failed — aborting calibration")
            sys.exit(1)
    print("\n✅ Calibration complete. Run normally to start relay check.")
    sys.exit(0)


# ── Main relay logic ─────────────────────────────────────────────────────────

def main():
    # ── Guard: images missing → snapshot + graceful exit ────────────────────
    if not images_ready():
        print("[main] Reference images not found. Sending snapshot to Discord.")
        msg = ("⚠️ BraveAutoRelay: Reference images missing in `images/`.\n"
               "Screenshot of current top-300px attached.\n\n"
               "Next step: run with `--calibrate` or manually save:\n"
               "• `relay_disabled.png`\n• `relay_enabled.png`\n• `tab_close.png`\n"
               f"into `{IMAGES_DIR}/`")
        discord_send(msg, snapshot())
        print("[main] Done — exiting until images are ready.")
        sys.exit(0)          # ← clean exit, not a crash

    print("🔄 BraveAutoRelay starting…")

    # Step 1: jump to first tab
    pyautogui.hotkey("ctrl", "1")
    time.sleep(0.6)

    region = top_region()

    # Record first tab's close-button position
    first_close = find(TAB_CLOSE, region)
    if not first_close:
        msg = "⚠️ BraveAutoRelay: Could not locate tab close button. Sending screenshot."
        discord_send(msg, snapshot(region))
        sys.exit(1)

    print(f"📍 First-tab X button at: {first_close}")
    on_count  = 0
    tab_index = 0
    MAX_TABS  = 50

    # Step 2-4: walk through tabs
    while tab_index < MAX_TABS:
        cur_close = find(TAB_CLOSE, region)

        # Detect wrap-around (back to first tab)
        if tab_index > 0 and cur_close:
            dx = abs(cur_close.left - first_close.left)
            dy = abs(cur_close.top  - first_close.top)
            if dx < 50 and dy < 10:
                print(f"  ↩ Wrapped back to first tab after {tab_index} iteration(s).")
                break

        # Look for disabled relay icon
        disabled = find(RELAY_DISABLED, region)
        if disabled:
            cx = pyautogui.center(disabled)
            print(f"  🔘 Disabled relay at {cx} — clicking…")
            pyautogui.click(cx)
            time.sleep(3)

            enabled = find(RELAY_ENABLED, region)
            if enabled:
                print(f"  ✅ ON badge confirmed at {pyautogui.center(enabled)}")
                on_count += 1
            else:
                print("  ⚠️  No ON badge appeared after click")
        else:
            print(f"  [tab {tab_index}] No disabled relay found")

        # Advance to next tab
        pyautogui.hotkey("ctrl", "tab")
        time.sleep(0.5)
        tab_index += 1
        region = top_region()

    # Step 5: result
    print(f"\n📊 Result: {on_count} ON badge(s) activated")

    if on_count >= 1:
        print(f"✅ Success — {on_count} relay tab(s) active.")
        discord_send(f"✅ BraveAutoRelay: {on_count} relay tab(s) attached successfully.")
        sys.exit(0)
    else:
        msg = "⚠️ BraveAutoRelay: No relay tab attached after full scan. Screenshot attached."
        discord_send(msg, snapshot(region))
        sys.exit(1)


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Ensure display is set (autostart might not inherit it)
    if not os.getenv("DISPLAY"):
        os.environ["DISPLAY"] = ":0"

    if "--snapshot" in sys.argv:
        snapshot_mode()
    elif "--calibrate" in sys.argv:
        calibrate_mode()
    else:
        try:
            main()
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(tb, file=sys.stderr)
            discord_send(f"🔴 BraveAutoRelay crashed:\n```{tb[:1800]}```", snapshot())
            sys.exit(1)
