# BraveAutoRelay

Automated utility to scan all open Brave browser tabs and activate any disabled [OpenClaw Browser Relay](https://docs.openclaw.ai) badges — then report results to Discord.

## What it does

1. Jumps to the first tab (`Ctrl+1`)
2. Walks through every open tab (`Ctrl+Tab`)
3. For each tab: looks for the **disabled relay icon** (via image recognition)
4. If found → clicks it and waits for the **enabled badge** to appear
5. Stops when it wraps back to the first tab
6. Posts a summary (or screenshot on failure) to a Discord channel

## Requirements

- Linux with a graphical display (X11, `DISPLAY=:0`)
- Brave browser with the OpenClaw Browser Relay extension installed
- Python 3.10+
- A Discord bot token (for status reporting)

## Setup

```bash
# Clone
git clone https://github.com/<your-username>/BraveAutoRelay.git
cd BraveAutoRelay

# Create virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.template .env
# Edit .env and set DISCORD_BOT_TOKEN
```

## Calibration (first-time setup)

The script uses reference images to locate UI elements on screen. Capture them once:

```bash
python3 BraveAutoRelay.py --calibrate
```

Follow the prompts to capture:
- `images/relay_disabled.png` — the disabled relay icon in the Brave toolbar
- `images/relay_enabled.png` — the enabled/ON relay badge
- `images/tab_close.png` — the tab close (×) button

Or use `--snapshot` to get a screenshot of the current top-300px sent to Discord for manual reference image extraction:

```bash
python3 BraveAutoRelay.py --snapshot
```

## Usage

```bash
# Normal run — scan all tabs and enable any disabled relays
python3 BraveAutoRelay.py

# Calibration mode — capture reference images interactively
python3 BraveAutoRelay.py --calibrate

# Snapshot mode — send a top-300px screenshot to Discord and exit
python3 BraveAutoRelay.py --snapshot
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DISCORD_BOT_TOKEN` | Yes | Discord bot token for status messages |

Discord channel ID is hardcoded to `#logs` (`1470284617151152261`). Edit `DISCORD_CHANNEL` in the script to change it.

## How it works

Uses [PyAutoGUI](https://pyautogui.readthedocs.io/) + OpenCV image matching (`locateOnScreen`) to detect UI elements in the top 300px of the screen (where browser tabs live). Confidence threshold is 0.8 by default.

Tab wrap detection: compares the position of the current tab's close button against the first tab's close button position. If they match within a tolerance of 50px (horizontal) and 10px (vertical), the scan is complete.

## Autostart (GNOME)

For fully automated recovery on every reboot, three autostart entries work together:

| Desktop entry | What it does | Timing |
|---|---|---|
| `reboot_recovery.desktop` | Clears Firefox/Brave stale locks, patches Brave prefs | Immediately at login |
| `claude-monitor.desktop` | Opens Firefox claude-monitor profile | `sleep 3` (after recovery) |
| `brave-auto-relay.desktop` | Polls until Brave is running, then scans tabs | Polls + `sleep 20` |

### Setup autostart

```bash
# 1. Reboot recovery (run first, clears stale locks + patches Brave)
cat > ~/.config/autostart/reboot_recovery.desktop << EOF
[Desktop Entry]
Type=Application
Name=RebootRecovery
Exec=bash /home/user/Code/BraveAutoRelay/reboot_recovery.sh
X-GNOME-Autostart-enabled=true
EOF

# 2. BraveAutoRelay (polls until Brave is actually running)
cat > ~/.config/autostart/brave-auto-relay.desktop << EOF
[Desktop Entry]
Type=Application
Name=Brave Auto Relay
Exec=bash -c "until pgrep -x brave > /dev/null; do sleep 3; done; sleep 20 && cd /home/user/Code/BraveAutoRelay && DISPLAY=:0 /home/user/Code/BraveAutoRelay/venv2/bin/python3 /home/user/Code/BraveAutoRelay/BraveAutoRelay.py"
X-GNOME-Autostart-enabled=true
EOF
```

### Additional one-time fixes (Ubuntu + GNOME)

```bash
# Disable screensaver lock (prevents GUI-blocking password dialog on auto-login)
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.screensaver ubuntu-lock-on-suspend false

# Fix GNOME Keyring auto-unlock: open seahorse, change "Login" keyring password to empty
seahorse
```

> **Note on snap Firefox**: Firefox snap stores its profile lock at
> `~/snap/firefox/common/.mozilla/firefox/` — not `~/.mozilla/firefox/`.
> `reboot_recovery.sh` clears both paths.

## File structure

```
BraveAutoRelay/
├── BraveAutoRelay.py        # Main script
├── reboot_recovery.sh       # Post-reboot: clear Firefox locks + patch Brave prefs
├── patch_brave_prefs.py     # Patch Brave: exit_type=Normal, restore_on_startup=1
├── requirements.txt         # Python dependencies
├── .env.template            # Environment variable template
├── .env                     # Your secrets (gitignored)
└── images/
    ├── relay_disabled.png   # Reference: disabled relay icon
    ├── relay_enabled.png    # Reference: enabled relay badge
    └── tab_close.png        # Reference: tab close button
```

## Notes

- `temp_screenshot.png` (written during runs) is gitignored
- If `DISPLAY` is not set, defaults to `:0` automatically (useful for autostart / cron)
- Crashes are caught and sent to Discord with a stack trace
- Brave prefs are backed up before each patch (`.bak.YYYYMMDD-HHMMSS` suffix)

## License

MIT
