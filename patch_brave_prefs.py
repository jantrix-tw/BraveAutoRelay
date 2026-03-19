import json, os, shutil
from datetime import datetime
PREFS = os.path.expanduser("~/.config/BraveSoftware/Brave-Browser/Default/Preferences")
if not os.path.exists(PREFS):
    print("[patch] Preferences not found"); exit(0)
shutil.copy2(PREFS, PREFS + ".bak." + datetime.now().strftime("%Y%m%d-%H%M%S"))
with open(PREFS) as f: prefs = json.load(f)
changed = []
if prefs.setdefault("profile", {}).get("exit_type") != "Normal":
    prefs["profile"]["exit_type"] = "Normal"; changed.append("exit_type=Normal")
if prefs.setdefault("session", {}).get("restore_on_startup") != 1:
    prefs["session"]["restore_on_startup"] = 1; changed.append("restore_on_startup=1")
if changed:
    with open(PREFS, "w") as f: json.dump(prefs, f, separators=(",",":"))
    print("[patch] Applied:", ", ".join(changed))
else:
    print("[patch] Already correct, no changes")
