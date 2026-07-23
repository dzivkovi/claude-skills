#!/usr/bin/env python3
"""Pandoc preflight: ensure pandoc is available before a Markdown -> EPUB conversion.

markdown-to-epub shells out to pandoc, which is its ONE external dependency (nothing
is bundled or auto-installed - installing a system package is invasive and package-
manager-specific). This checks pandoc is on PATH and, when it is not, fails LOUD with
OS-specific install guidance so a fresh clone of this skill tells the user exactly what
to install instead of erroring cryptically mid-conversion. Guidance, not force-install
(mirrors branded-docx/font_preflight.py's Windows manual-step philosophy).

Exit codes: 0 = pandoc resolves (prints its version); 2 = pandoc is not installed.

Usage: python pandoc_preflight.py
"""
import platform, shutil, subprocess, sys

def log(msg): print(f"[pandoc-preflight] {msg}", file=sys.stderr)

INSTALL = {
    "Windows": [
        "winget install --id JohnMacFarlane.Pandoc -e",
        "choco install pandoc",
        "scoop install pandoc",
    ],
    "Darwin": [
        "brew install pandoc",
        "sudo port install pandoc",
    ],
    "Linux": [
        "sudo apt-get install pandoc      # Debian/Ubuntu",
        "sudo dnf install pandoc          # Fedora/RHEL",
        "sudo pacman -S pandoc            # Arch",
    ],
}

def main():
    exe = shutil.which("pandoc")
    if exe:
        try:
            ver = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.splitlines()[0]
        except Exception:
            ver = "pandoc (version unknown)"
        log(f"OK: {ver} at {exe}")
        return 0
    log("FAIL: pandoc is not installed or not on PATH. It is the only dependency this skill needs.")
    for cmd in INSTALL.get(platform.system(), []):
        log(f"  install: {cmd}")
    log("  or download a package from https://pandoc.org/installing.html")
    log("Re-run this preflight after installing to confirm.")
    return 2

if __name__ == "__main__":
    sys.exit(main())
