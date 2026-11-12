---
name: rescue
description: "Hand one question or investigation to Google's Gemini as an independent, read-only expert. By default Gemini reads the repository itself through the Gemini CLI (repo mode); it falls back to a single file Claude writes (file mode) when repo mode is unavailable. --resume continues the last Gemini session. Use for '/gemini:rescue', 'ask Gemini', 'what does Gemini think', 'Gemini's view', 'get a third opinion', 'have Gemini dig into this', 'Gemini dig deeper'. With 'ask both' or 'all experts', run the Codex rescue in parallel. For a review of the current diff, use /gemini:review instead. Not for a bare 'second opinion' or 'ask Codex' (those stay with the Codex plugin). Never writes code."
argument-hint: "[--resume [session-id]] [--file-only] [--model <alias|id>] [--thinking low|high] <ask>"
allowed-tools: Bash, Write, Read, Agent
---

# Gemini rescue

One question to Gemini, read-only. Return Gemini's answer verbatim, then your own read under its own heading. Never apply what it suggests unless the user asks afterwards. If the ask is a review of the current diff, use `/gemini:review` instead.

## Pick the mode

- `--file-only` given: file mode.
- Otherwise repo mode. If the script exits 3 (repo mode unavailable), say in one line why (the reason it printed) and rerun the same ask in file mode. If the user asked for `--resume`, say that the resume was dropped with the fallback.
- Exit 1 from repo mode is an error to report, not a reason to fall back.

## Repo mode

Write a short brief **outside the repo** (the session scratchpad or the OS temp folder, never the working tree, or the tree-change check fails):

```markdown
# Ask
<the user's question, precise>
## Context
<two or three sentences: what the user is doing and why it matters>
## Start here
<the files or folders most likely relevant, as paths relative to the repository root>
## Rules to read first
<CLAUDE.md, AGENTS.md and any path-scoped rule files the question touches, as paths: the Gemini CLI does not load them by itself>
```

Keep the material in the brief, not in arguments, and name the files to start with: a vague brief makes Gemini wander. The script runs the CLI from the git root whatever your current folder is.

**Always run repo mode with Bash `run_in_background: true`.** A run can take 10 minutes or more (the script stops it at 20), longer than the 600 s foreground limit. You are notified when it exits; then read the three files. Run the whole block as one Bash call: variables do not carry over between calls.

```bash
for c in python3 python "py -3"; do $c -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1 && { PY="$c"; break; }; done
[ -n "$PY" ] || { echo "No Python 3.10+ found (tried python3, python, py -3)."; exit 1; }
G="${CLAUDE_PLUGIN_ROOT}/scripts/gemini_review.py"
$PY "$G" --repo --brief "<brief file>" [--model <m>] [--resume <session-id>] > "<scratch>/gemini-out.md" 2> "<scratch>/gemini-err.txt"
echo "exit=$?" > "<scratch>/gemini-exit.txt"
```

If `${CLAUDE_PLUGIN_ROOT}` is empty, set `G` to `../../scripts/gemini_review.py` resolved from this skill's base directory. Never chain interpreters with `||`: the script's exit codes would trigger the next one.

For `--resume`, pass the `session=<id>` value from the last run's `gemini_review:` stderr line when you have one (`--resume <id>`), so the script never continues a session the user started by hand. Never pass `--resume None`. Without an id, `--resume` alone means the latest session in this directory and fails loudly if there is none.

## File mode

Write one self-contained scratch file outside the repo with the ask, the context, and the relevant code quoted in fenced blocks (never gitignored files, `.env` values or secrets). File mode may run in the foreground with Bash `timeout: 600000`:

```bash
for c in python3 python "py -3"; do $c -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1 && { PY="$c"; break; }; done
[ -n "$PY" ] || { echo "No Python 3.10+ found (tried python3, python, py -3)."; exit 1; }
$PY "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_review.py" --file "<scratch file>" [--model <m>] [--thinking <t>]
```

## Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | answer printed | show it |
| 1 | key missing, CLI or HTTP error, bad model id, no session to resume | show stderr; suggest `/gemini:setup` |
| 2 | usage error, or Python could not open the script | show stderr; if it says "can't open file", recompute `G` from this skill's base directory |
| 3 | repo mode unavailable | one line why, then file mode |
| 4 | the working tree changed during a read-only run | show the answer AND warn loudly with the paths it printed; the cause can be Gemini, Codex in an "ask both" run, the user editing, or you |
| 5 | unknown model alias | show the available list it printed |

## Answer shape

- `## Gemini's answer`: stdout verbatim, then the `gemini_review: mode=... model=... session=...` line from stderr.
- `## Claude's read`: agreements, disagreements with reasons, and what still needs checking.

## Ask both

On "ask both" or "all experts", start the `codex:codex-rescue` agent (Agent tool) and this script in background Bash in the same message, then present both answers and your read as three sections. Do not edit files while Gemini runs, or the tree-change check fires.

## Confidentiality

What Gemini receives leaves the machine for Google's API. Never send gitignored paths, secrets, `.env` values or personal data. A project can add a stricter rule in its own `CLAUDE.md`, and that rule wins. Repo mode runs the CLI in its read-only plan mode with a bundled allow-list policy (`read_file`, `list_directory`, `glob` only), passes git's own ignored list to the CLI, refuses repos that carry `.gemini/settings.json` or links into ignored paths, and leaves a session transcript under `~/.gemini/tmp/`. The script reads the key from `GEMINI_API_KEY` and never prints it.
