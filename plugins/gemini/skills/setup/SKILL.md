---
name: setup
description: "Check whether the Gemini plugin is ready: Python 3.10+, GEMINI_API_KEY, the resolved default model and thinking level, and whether git is available for --repo. Use for '/gemini:setup', 'is Gemini set up', 'check my Gemini key'. Not for Codex setup (that is /codex:setup)."
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
$PY "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_review.py" --setup [--model <m>]
```

Add `--model <m>` only when the user named a model; never paste the raw slash-command arguments into the shell. If `${CLAUDE_PLUGIN_ROOT}` is empty, the script is at `../../scripts/gemini_review.py` relative to this skill's base directory.

## Reading the result

- Exit 0: ready. The output names the model (`carbon -> <id>, thinking high`) and whether git is found (needed only for `--repo`).
- Exit 1 with `GEMINI_API_KEY is not set`: show the one-line fix exactly as printed. On Windows `setx` only reaches new shells, so the user must restart Claude Code after it. The key is read from the environment on every run and never stored or printed.
- Exit 1 with `cannot list models: HTTP ...`: the key is invalid or the network is down; show stderr.
- Exit 2: a usage error, or Python could not open the script (recompute the path from this skill's base directory). Exit 5: the `--model` alias matched nothing; show the available list it printed.

Say which interpreter was used (`$PY`).

## Confidentiality

What Gemini receives leaves the machine for Google's API. Never send gitignored paths, secrets, `.env` values or personal data. A project can add a stricter rule in its own `CLAUDE.md`, and that rule wins. The script reads the key from `GEMINI_API_KEY` and never prints it.
