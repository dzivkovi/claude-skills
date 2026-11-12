---
name: review
description: "Ask Google's Gemini to review the current diff (working tree, or <base>...HEAD) as an outside reviewer and return numbered findings with severities, then Claude's own read. Never applies fixes. Use for '/gemini:review', 'ask Gemini to review this', 'Gemini review', 'Gemini's view on this diff', 'third opinion on this change', 'adversarial review with Gemini'. With 'ask both' or 'all experts', also run the Codex review in parallel. Not for a bare 'second opinion' or 'ask Codex' (those stay with the Codex plugin)."
argument-hint: "[--base <ref>] [--model <alias|id>] [--thinking low|high] [focus ...]"
allowed-tools: Bash, Write, Read
---

# Gemini review

Gemini sees one self-contained file that you write. It does not read the repo. Return its findings verbatim, then your own read, and never apply fixes.

## Steps

1. **Collect the diff.** With `--base <ref>`: `git diff <ref>...HEAD`. Otherwise the working tree: `git diff HEAD` plus the content of new untracked files that are not gitignored (`git ls-files --others --exclude-standard`). Never include gitignored files, `.env` values or secrets; if the diff touches such content, drop those hunks and say so.
2. **Write one scratch file outside the repo** (the session scratchpad or the OS temp folder, never the working tree), in this shape:

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
   ## Diff
   <the diff in a fenced block>
   ```

3. **Run file mode** with the interpreter rule below. Use Bash `timeout: 600000`, or `run_in_background: true` for a large diff or when running beside Codex.

   ```bash
   for c in python3 python "py -3"; do $c -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1 && { PY="$c"; break; }; done
   $PY "${CLAUDE_PLUGIN_ROOT}/scripts/gemini_review.py" --file "<scratch file>" [--model <m>] [--thinking <t>]
   ```

   If `${CLAUDE_PLUGIN_ROOT}` is empty, the script is at `../../scripts/gemini_review.py` relative to this skill's base directory. Never chain interpreters with `||`.

4. **Answer in two clearly separated parts:**
   - `## Gemini's findings`: stdout verbatim, then the `gemini_review: mode=file model=... usage=...` token line from stderr.
   - `## Claude's read`: where you agree, disagree (with the reason), and anything Gemini could not judge from the file alone. Do not edit any file.

## Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | answer printed | show it |
| 1 | key missing, HTTP error, rejected model | show stderr; suggest `/gemini:setup` |
| 2 | unknown model alias | show the available list it printed |

## Ask both

On "ask both" or "all experts", start the Codex review (`codex:codex-rescue` agent or `/codex:review`) and this script in background Bash in the same message, then present Gemini's findings, Codex's findings and your read as three sections.

## Confidentiality

What Gemini receives leaves the machine for Google's API. Never send gitignored paths, secrets, `.env` values or personal data. A project can add a stricter rule in its own `CLAUDE.md`, and that rule wins. File mode does no gitignore check of its own: what you put in the scratch file is what is sent. The script reads the key from `GEMINI_API_KEY` and never prints it.
