#!/usr/bin/env python3
"""Print the current user's Downloads directory, OS-agnostically (creates it if absent).

markdown-to-epub drops a copy of the finished .epub here so it is easy to
Send-to-Kindle, in addition to the canonical copy next to the source. Never
hardcode a path: Linux honors the XDG user-dirs config (localized or relocated
Downloads); Windows, macOS, and the Linux fallback use ~/Downloads (which on
Windows Git Bash resolves under %USERPROFILE%).

Usage: DL="$(python downloads_dir.py)"; cp note.epub "$DL/"
"""
import os, subprocess, sys
from pathlib import Path

def downloads_dir():
    if sys.platform.startswith("linux"):
        try:
            out = subprocess.run(["xdg-user-dir", "DOWNLOAD"],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
            if out and os.path.isdir(out):
                return out
        except Exception:
            pass
    return str(Path.home() / "Downloads")

if __name__ == "__main__":
    d = downloads_dir()
    os.makedirs(d, exist_ok=True)
    print(d)
