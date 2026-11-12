---
name: review
description: "Ask Google's Gemini to review the current diff (working tree, or <base>...HEAD) as an outside reviewer and return numbered findings with severities, then Claude's own read. Never applies fixes. Use for '/gemini:review', 'ask Gemini to review this', 'Gemini review', 'Gemini's view on this diff', 'third opinion on this change', 'adversarial review with Gemini'. With 'ask both' or 'all experts', also run the Codex review in parallel. Not for a bare 'second opinion' or 'ask Codex' (those stay with the Codex plugin)."
argument-hint: "[--base <ref>] [--repo <paths...>] [--model <alias|id>] [--thinking low|high] [focus ...]"
allowed-tools: Bash, Write, Read, Agent
---

# Gemini review

Gemini sees the brief you write, the diff the script builds from files git allows, and, with `--repo`, whole repository files you name, each checked by git first. Return its findings verbatim, then your own read, and never apply fixes.

## Steps

1. **Let the script build the diff.** Pass `--diff` for the working tree against `HEAD`, or `--diff <base>` for `<base>...HEAD`. The script lists the changed files, runs each through the same git check as `--repo` (ignored, force-added past `.gitignore`, secret file names, encrypting filters, links), builds the diff from the allowed files only with textconv off, and names the left-out files on stderr. **Do not paste `git diff` output into the brief yourself**: a raw diff carries hunks of files the check would refuse. New untracked files are not in `git diff HEAD`; add the ones that matter with `--repo <path>`.
2. **Write one brief outside the repo** (the session scratchpad or the OS temp folder, never the working tree). It is sent as written and is outside the git check, so it holds context, not code from ignored files:

   ```markdown
   # Review request
   ## Intent
   <what the change is for, in two or three sentences>
   ## Already applied by earlier reviews
   <what other reviewers already caught and fixed, so Gemini does not repeat it; "none" if none>
   ## Focus
   <the user's focus text, or "general correctness, security and design">
   ## Rules that apply
   <the relevant lines from the repo's CLAUDE.md / AGENTS.md / path-scoped rule files, quoted, because Gemini sees none of them>
   ```

3. **Optionally add whole files** with `--repo <paths>` when the diff alone hides the context (a changed function's callers, the file a hunk sits in). Paths are relative to the repository root. If any named file is refused, nothing is sent (exit 3): drop that path and run again.
4. **Run it** from inside the repository as one Bash call with `run_in_background: true` (variables do not carry over between calls; a large diff with thinking high can take several minutes):

   ```bash
   for c in python3 python "py -3"; do $c -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1 && { PY="$c"; break; }; done
   [ -n "$PY" ] || { echo "No Python 3.10+ found (tried python3, python, py -3)."; exit 1; }
   $PY "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_review.py" --file "<brief>" --diff [<base>] [--repo <path> ...] [--model <m>] [--thinking <t>] > "<scratch>/gemini-out.md" 2> "<scratch>/gemini-err.txt"
   echo "exit=$?" > "<scratch>/gemini-exit.txt"
   ```

   If `${CLAUDE_PLUGIN_ROOT}` is empty, use `../../scripts/gemini_review.py` resolved from this skill's base directory. Never chain interpreters with `||`: the script's exit codes would trigger the next one. Add `--dry-run` first if you want to see what would be sent.

5. **Answer in two clearly separated parts:**
   - `## Gemini's findings`: stdout verbatim, then the `gemini_review: mode=... model=... usage=...` token line from stderr, and any "left out of the diff" lines.
   - `## Claude's read`: where you agree, disagree (with the reason), and anything Gemini could not judge. Do not edit any file.

## Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | answer printed | show it |
| 1 | key missing, brief file missing or unreadable, HTTP error, rejected model | show stderr; for a key or HTTP problem suggest `/gemini:setup` |
| 2 | usage error, or Python could not open the script | show stderr; if it says "can't open file", recompute the path from this skill's base directory |
| 3 | `--diff` or `--repo` refused, or not in a git repo or git failed; nothing was sent | drop or replace the refused paths and run again; never copy refused content into the brief |
| 5 | unknown model alias | show the available list it printed |

## Ask both

On "ask both" or "all experts", start the `codex:codex-rescue` agent (Agent tool) with a review-only ask about the same diff, and this script in background Bash, in the same message. Then present Gemini's findings, Codex's findings and your read as three sections.

## Confidentiality

What Gemini receives leaves the machine for Google's API. Never send gitignored paths, secrets, `.env` values or personal data. A project can add a stricter rule in its own `CLAUDE.md`, and that rule wins. The brief is your responsibility; `--repo` files pass git's check first. The script reads the key from `GEMINI_API_KEY` and never prints it.
