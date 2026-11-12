---
name: rescue
description: "Hand one question or investigation to Google's Gemini as an independent, read-only expert. Claude writes a brief; with --repo, Claude also names the repository files Gemini should see, and the script attaches only files git says are shareable. Use for '/gemini:rescue', 'ask Gemini', 'what does Gemini think', 'Gemini's view', 'get a third opinion', 'have Gemini dig into this'. With 'ask both' or 'all experts', run the Codex rescue in parallel. For a review of the current diff, use /gemini:review instead. Not for a bare 'second opinion' or 'ask Codex' (those stay with the Codex plugin). Never writes code."
argument-hint: "[--repo <paths...>] [--model <alias|id>] [--thinking low|high] <ask>"
allowed-tools: Bash, Write, Read, Agent
---

# Gemini rescue

One question to Gemini, read-only. Return Gemini's answer verbatim, then your own read under its own heading. Never apply what it suggests unless the user asks afterwards. If the ask is a review of the current diff, use `/gemini:review` instead.

## What Gemini sees

You decide, and git checks:

- **The brief** (always): one file you write **outside the repo** (the session scratchpad or the OS temp folder). It is sent exactly as written, so put in only what Gemini needs: the ask, the context, short quoted code. **Never paste gitignored content, `.env` values, secrets, personal data or client names into it**: the brief is outside the git check.
- **Repository files** (`--repo`, when the ask needs real code): name the files or folders, as paths relative to the repository root. The script reads them itself (your context does not grow), and it attaches a file only when git lists it as shareable: tracked, or untracked and not ignored, not matched by `.gitignore` or an exclude file, not a secret file name, not a link. A folder brings in its tracked files only; name untracked files one by one. **If any file you named is refused, nothing is sent** (exit 3): read the reasons, drop or replace those paths, and run again.

Pick the smallest set that answers the ask. Start with `--dry-run` when you name a folder, to see what it expands to.

## The brief

```markdown
# Ask
<the user's question, precise>
## Context
<two or three sentences: what the user is doing and why it matters>
## Rules that apply
<the lines from CLAUDE.md, AGENTS.md or path-scoped rule files that bear on the question, quoted: Gemini sees none of them otherwise>
```

## Run it

**Always use Bash `run_in_background: true`** and one Bash call for the whole block (variables do not carry over between calls). With thinking high a request can take several minutes; the script allows 15. You are notified when it exits; then read the three files.

```bash
for c in python3 python "py -3"; do $c -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1 && { PY="$c"; break; }; done
[ -n "$PY" ] || { echo "No Python 3.10+ found (tried python3, python, py -3)."; exit 1; }
$PY "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_review.py" --file "<brief file>" [--repo <path> ...] [--model <m>] [--thinking <t>] > "<scratch>/gemini-out.md" 2> "<scratch>/gemini-err.txt"
echo "exit=$?" > "<scratch>/gemini-exit.txt"
```

Run it from inside the repository when you use `--repo`. If `${CLAUDE_PLUGIN_ROOT}` is empty, use `../../scripts/gemini_review.py` resolved from this skill's base directory. Never chain interpreters with `||`: the script's exit codes would trigger the next one.

## Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | answer printed | show it |
| 1 | key missing, HTTP error, bad model id | show stderr; suggest `/gemini:setup` |
| 2 | usage error, or Python could not open the script | show stderr; if it says "can't open file", recompute the path from this skill's base directory |
| 3 | `--repo` refused a file (or not in a git repo); nothing was sent | read the reasons, narrow the paths or move the needed content into the brief yourself, run again |
| 5 | unknown model alias | show the available list it printed |

## Answer shape

- `## Gemini's answer`: stdout verbatim, then the `gemini_review: mode=... model=... usage=...` line from stderr.
- `## Claude's read`: agreements, disagreements with reasons, and what still needs checking.

## Ask both

On "ask both" or "all experts", start the `codex:codex-rescue` agent (Agent tool) and this script in background Bash in the same message, then present both answers and your read as three sections.

## Confidentiality

What Gemini receives leaves the machine for Google's API. Never send gitignored paths, secrets, `.env` values or personal data. A project can add a stricter rule in its own `CLAUDE.md`, and that rule wins. The brief is your responsibility; `--repo` files pass git's check first. The script reads the key from `GEMINI_API_KEY` and never prints it.
