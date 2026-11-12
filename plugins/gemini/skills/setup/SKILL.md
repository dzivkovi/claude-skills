---
name: setup
description: "Check whether the Gemini plugin is ready: Python 3.10+, GEMINI_API_KEY, the resolved default model and thinking level, the Gemini CLI version, and whether repo mode is available here. Use for '/gemini:setup', 'is Gemini set up', 'check my Gemini key', 'why does gemini rescue fall back to file mode'. Not for Codex setup (that is /codex:setup)."
argument-hint: "[--model <alias|id>]"
allowed-tools: Bash
---

# Gemini setup

Run the readiness check and show its output to the user as is.

## Command

Pick the interpreter once: the first of `python3`, `python`, `py -3` that is Python 3.10 or later. Do not chain them with `||`, because the script's own exit codes would trigger the next one.

```bash
for c in python3 python "py -3"; do $c -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1 && { PY="$c"; break; }; done
[ -n "$PY" ] || { echo "No Python 3.10+ found (tried python3, python, py -3)."; exit 1; }
$PY "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_review.py" --setup $ARGUMENTS
```

If `${CLAUDE_PLUGIN_ROOT}` is empty, the script is at `../../scripts/gemini_review.py` relative to this skill's base directory.

## Reading the result

- Exit 0: ready. The output names the model (`carbon -> <id>, thinking high`), the CLI version, and whether repo mode is available.
- Exit 1 with `GEMINI_API_KEY is not set`: show the one-line fix exactly as printed. On Windows `setx` only reaches new shells, so the user must restart Claude Code after it.
- Repo mode is used only by `/gemini:rescue`; `/gemini:review` always uses file mode, so do not say review "can use repo mode".
- `repo mode: unavailable`: `/gemini:rescue` still works in file mode. Show the reason; offer `npm i -g @google/gemini-cli` only when the CLI is missing.
- Exit 2: a usage error, or Python could not open the script (recompute the path from this skill's base directory). Exit 5: the `--model` alias matched nothing; show the available list it printed.

Say which interpreter was used (`$PY`).

## Confidentiality

What Gemini receives leaves the machine for Google's API. Never send gitignored paths, secrets, `.env` values or personal data. A project can add a stricter rule in its own `CLAUDE.md`, and that rule wins. The script reads the key from `GEMINI_API_KEY` and never prints it.
