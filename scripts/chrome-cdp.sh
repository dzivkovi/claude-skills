#!/usr/bin/env bash
# chrome-cdp.sh - start, check, or kill a Chrome instance dedicated to
# CDP (Chrome DevTools Protocol) browser automation.
#
# WHY THIS EXISTS: any CDP client (the chrome-cdp MCP server, the
# agent-browser CLI, a custom script) just connects to whatever process
# answers on the debug port. It has no way to tell your intended browser
# apart from a stray one left running by an unrelated project or session.
# That happened for real: an orphaned headless Chrome from a different
# project sat on port 9222 for over a day, and both a `chrome-cdp` health
# check and an agent connecting to "port 9222" trusted it as healthy,
# because it answered fast enough. Full writeup: README.md in this folder.
#
# This script's one job: never trust "something answers on the port" as
# proof it's YOUR browser. Verify the process's own command line matches
# your profile directory before calling it healthy.
#
# Usage:
#   source scripts/chrome-cdp.sh        # defines the chrome-cdp() function
#   chrome-cdp [start|status|kill|restart]   # default action: start
#
# Or run it standalone without sourcing (same subcommands):
#   ./scripts/chrome-cdp.sh status
#
# Config (override via env vars before sourcing/running):
#   CHROME_CDP_PORT     debug port (default 9222)
#   CHROME_CDP_PROFILE  dedicated user-data-dir (default: see OS block below)
#
# Tested primary: Windows + Git Bash (MINGW64). macOS/Linux branches are
# believed correct but far less battle-tested than the Windows path -
# please report back (or send a PR) if something's off.

_CHROME_CDP_PORT="${CHROME_CDP_PORT:-9222}"

case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*)
    _CHROME_CDP_OS="windows"
    _CHROME_CDP_BIN="/c/Program Files/Google/Chrome/Application/chrome.exe"
    # Native Windows backslash form, via cygpath: chrome.exe reports its own
    # --user-data-dir back in this form (Get-CimInstance CommandLine), so the
    # launch value and the comparison value must both be built this way or
    # _chrome-cdp-is-mine silently fails to match a browser this script itself
    # started (POSIX /c/Users/... vs Windows C:\Users\... never grep-match).
    _CHROME_CDP_PROFILE="${CHROME_CDP_PROFILE:-$(cygpath -w "$HOME/.config/chrome-cdp-profile" 2>/dev/null || echo "$HOME/.config/chrome-cdp-profile")}"
    ;;
  Darwin)
    _CHROME_CDP_OS="macos"
    _CHROME_CDP_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    _CHROME_CDP_PROFILE="${CHROME_CDP_PROFILE:-${TMPDIR:-/tmp}/chrome-cdp-profile}"
    ;;
  *)
    _CHROME_CDP_OS="linux"
    _CHROME_CDP_BIN="$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || command -v chromium-browser)"
    _CHROME_CDP_PROFILE="${CHROME_CDP_PROFILE:-${TMPDIR:-/tmp}/chrome-cdp-profile}"
    ;;
esac

# --- PID of whatever is listening on the debug port, if anything ---
_chrome-cdp-pid() {
  case "$_CHROME_CDP_OS" in
    windows)
      netstat -ano 2>/dev/null \
        | grep -E "127\.0\.0\.1:${_CHROME_CDP_PORT}[[:space:]].*LISTENING" \
        | awk '{print $NF}' | head -1
      ;;
    *)
      # macOS/Linux: needs lsof. Untested against a real stray-process case.
      lsof -ti "tcp:${_CHROME_CDP_PORT}" -sTCP:LISTEN 2>/dev/null | head -1
      ;;
  esac
}

# --- Full command line of a PID, so we can check whose profile it is ---
_chrome-cdp-cmdline() {
  local pid="$1"
  case "$_CHROME_CDP_OS" in
    windows)
      # netstat/tasklist don't expose the command line; WMI does.
      powershell.exe -NoProfile -Command \
        "(Get-CimInstance Win32_Process -Filter \"ProcessId=$pid\").CommandLine" 2>/dev/null
      ;;
    *)
      ps -p "$pid" -o command= 2>/dev/null
      ;;
  esac
}

# --- The actual safety check: is the port answering FROM YOUR profile? ---
_chrome-cdp-is-mine() {
  _chrome-cdp-cmdline "$1" | grep -qF "$_CHROME_CDP_PROFILE"
}

_chrome-cdp-kill-pid() {
  local pid="$1"
  case "$_CHROME_CDP_OS" in
    windows) powershell.exe -NoProfile -Command "Stop-Process -Id $pid -Force" 2>/dev/null ;;
    *) kill -9 "$pid" 2>/dev/null ;;
  esac
}

chrome-cdp() {
  local action="${1:-start}"
  local pid; pid=$(_chrome-cdp-pid)

  case "$action" in
    status)
      if [ -z "$pid" ]; then
        echo "chrome-cdp: nothing on $_CHROME_CDP_PORT"
        return 0
      fi
      if _chrome-cdp-is-mine "$pid"; then
        echo "chrome-cdp: your profile, healthy (pid $pid)"
      else
        echo "chrome-cdp: STRAY process on $_CHROME_CDP_PORT (pid $pid), not your profile:"
        _chrome-cdp-cmdline "$pid"
      fi
      ;;
    kill)
      if [ -z "$pid" ]; then
        echo "chrome-cdp: nothing to kill on $_CHROME_CDP_PORT"
        return 0
      fi
      echo "chrome-cdp: killing pid $pid on $_CHROME_CDP_PORT"
      _chrome-cdp-kill-pid "$pid"
      sleep 1
      if [ -z "$(_chrome-cdp-pid)" ]; then
        echo "chrome-cdp: port $_CHROME_CDP_PORT is free"
      else
        echo "chrome-cdp: still occupied, check manually"
      fi
      ;;
    restart)
      chrome-cdp kill
      chrome-cdp start
      ;;
    start)
      if [ -n "$pid" ]; then
        if _chrome-cdp-is-mine "$pid"; then
          echo "already up: $(curl -s -m 2 "http://127.0.0.1:${_CHROME_CDP_PORT}/json/version" | grep -oE '"Browser":[[:space:]]*"[^"]*"')"
        else
          echo "chrome-cdp: port $_CHROME_CDP_PORT is held by something ELSE (pid $pid), not your profile:"
          _chrome-cdp-cmdline "$pid"
          echo "chrome-cdp: run 'chrome-cdp kill' to free it, then 'chrome-cdp' again"
          return 1
        fi
        return 0
      fi
      "$_CHROME_CDP_BIN" \
        --remote-debugging-port="$_CHROME_CDP_PORT" \
        --user-data-dir="$_CHROME_CDP_PROFILE" >/dev/null 2>&1 &
      sleep 2
      local ver; ver=$(curl -s -m 3 "http://127.0.0.1:${_CHROME_CDP_PORT}/json/version")
      if [ -n "$ver" ]; then
        echo "chrome-cdp up on $_CHROME_CDP_PORT"
      else
        echo "chrome-cdp FAILED to start"
      fi
      ;;
    *)
      echo "usage: chrome-cdp [start|status|kill|restart]"
      return 1
      ;;
  esac
}

# Runnable standalone (./scripts/chrome-cdp.sh status) as well as sourced.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  chrome-cdp "$@"
fi
