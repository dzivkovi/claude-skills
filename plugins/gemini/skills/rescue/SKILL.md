---
name: rescue
description: "Hand one question or investigation to Google's Gemini as an independent, read-only expert. By default Gemini reads the repository itself through the Gemini CLI (repo mode); it falls back to a single file Claude writes (file mode) when repo mode is unavailable. --resume continues the last Gemini session. Use for '/gemini:rescue', 'ask Gemini', 'what does Gemini think', 'Gemini's view', 'get a third opinion', 'have Gemini dig into this', 'Gemini dig deeper'. With 'ask both' or 'all experts', run the Codex rescue in parallel. Not for a bare 'second opinion' or 'ask Codex' (those stay with the Codex plugin). Never writes code."
argument-hint: "[--resume [session-id]] [--file-only] [--model <alias|id>] [--thinking low|high] <ask>"
allowed-tools: Bash, Write, Read
---

# Gemini rescue

One question to Gemini, read-only. Return Gemini's answer verbatim, then your own read under its own heading. Never apply what it suggests unless the user asks afterwards.

## Pick the mode

- `--file-only` given: file mode.
- Otherwise repo mode. If the script exits 3 (repo mode unavailable), say in one line why (the reason it printed) and rerun the same ask in file mode.
- Exit 1 from repo mode is an error to report, not a reason to fall back.

## Interpreter and script

```bash
for c in python3 python "py -3"; do $c -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1 && { PY="$c"; break; }; done
G="${CLAUDE_PLUGIN_ROOT}/scripts/gemini_review.py"
```

If `${CLAUDE_PLUGIN_ROOT}` is empty, the script is at `../../scripts/gemini_review.py` relative to this skill's base directory. Never chain interpreters with `||`: the script's exit codes would trigger the next one.

**Always run repo mode with Bash `run_in_background: true`** and redirect stdout and stderr to two files in the scratch folder; you are notified when it exits, then read both files. A repo-mode run can take 10 minutes or more (the script stops it at 20), longer than the 600 s foreground limit. File mode may run in the foreground with `timeout: 600000`.

## Repo mode

Write a short brief **outside the repo** (the session scratchpad or the OS temp folder, never the working tree, or the tree-change check fails):

```markdown
# Ask
<the user's question, precise>
## Context
<two or three sentences: what the user is doing and why it matters>
## Start here
<the files or folders most likely relevant, as repo-relative paths>
## Rules to read first
<CLAUDE.md, AGENTS.md and any path-scoped rule files the question touches, as paths: the Gemini CLI does not load them by itself>
```

Keep the material in the brief, not in arguments. Name the files to start with: Gemini reads what it needs and a vague brief makes it wander. Then, from the repo root, in background Bash:

```bash
$PY "$G" --repo --brief "<brief file>" [--model <m>] > "<scratch>/gemini-out.md" 2> "<scratch>/gemini-err.txt"
```

For `--resume`, pass the `session=<id>` value from the last run's `gemini_review:` stderr line when you have it (`--resume <id>`), so the script never continues a session the user started by hand. Without an id, `--resume` alone means the latest session in this directory and fails loudly if there is none.

## File mode

Write one self-contained scratch file outside the repo with the ask, the context, and the relevant code quoted in fenced blocks (never gitignored files, `.env` values or secrets). Then:

```bash
$PY "$G" --file "<scratch file>" [--model <m>] [--thinking <t>]
```

## Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | answer printed | show it |
| 1 | key missing, CLI or HTTP error, bad model id, no session to resume | show stderr; suggest `/gemini:setup` |
| 2 | unknown model alias | show the available list it printed |
| 3 | repo mode unavailable | one line why, then file mode |
| 4 | the working tree changed during a read-only run | show the answer AND warn loudly with the paths it printed; the user must inspect them |

## Answer shape

- `## Gemini's answer`: stdout verbatim, then the `gemini_review: mode=... model=... session=...` line from stderr.
- `## Claude's read`: agreements, disagreements with reasons, and what still needs checking.

## Ask both

On "ask both" or "all experts", start the `codex:codex-rescue` agent and this script in background Bash in the same message, then present both answers and your read as three sections. If repo mode exits 4 while Codex was running, say that Codex may have made the change.

## Confidentiality

What Gemini receives leaves the machine for Google's API. Never send gitignored paths, secrets, `.env` values or personal data. A project can add a stricter rule in its own `CLAUDE.md`, and that rule wins. Repo mode runs the CLI in its read-only plan mode with a bundled allow-list policy (`read_file`, `list_directory`, `glob` only, gitignore filtering kept on), refuses repos that carry `.gemini/settings.json`, and leaves a session transcript under `~/.gemini/tmp/`. The script reads the key from `GEMINI_API_KEY` and never prints it.
