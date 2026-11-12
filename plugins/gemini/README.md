# gemini: Gemini as a third expert in Claude Code

Ask Google's Gemini for an outside review or a third opinion with the same command shape as the OpenAI Codex plugin, so "ask Gemini" and "ask Codex" route the same way:

| Codex plugin | This plugin |
|---|---|
| `/codex:rescue` | `/gemini:rescue`: one read-only question to Gemini, with the repository files Claude names |
| `/codex:review`, `/codex:adversarial-review` | `/gemini:review [focus]`: Gemini reviews the current diff; the focus text covers adversarial reviews |
| `/codex:setup` | `/gemini:setup`: readiness check, no hook |

It is deliberately small: three skills and one standard-library Python script that calls the Gemini REST API. No hooks, no Node, no Gemini CLI, no background job store, no subagent.

## Install

```text
/plugin marketplace add dzivkovi/claude-skills
/plugin install gemini@dzivkovi
```

On Claude Code 2.1.275 or later this is one step: `/plugin install gemini --marketplace dzivkovi/claude-skills`.

You need Python 3.10 or later, a Gemini API key from Google AI Studio in `GEMINI_API_KEY`, and git for `--repo`:

- Windows: `setx GEMINI_API_KEY "<your key>"`, then restart Claude Code (`setx` only reaches new shells).
- macOS and Linux: add `export GEMINI_API_KEY=<your key>` to your shell profile, then open a new shell.

The key is read from the environment on every run. It is never stored, written to a file or printed. Run `/gemini:setup` to check everything; it prints the resolved model, for example `carbon -> gemini-4-carbon, thinking high`.

## What Gemini sees

Claude decides what leaves the machine, and git checks the files:

| Part | Who picks it | What checks it |
|---|---|---|
| **The brief** (always) | Claude writes one file: the ask, the context, the diff, short quoted code | Claude, under your `CLAUDE.md` rules. It is sent exactly as written. |
| **The diff** (`--diff [base]`, used by `/gemini:review`) | the script lists the changed files | the same git check, file by file; refused files are left out of the diff and named |
| **Repository files** (`--repo <paths>`) | Claude names files or folders, relative to the repository root | git, before anything is sent (below) |

A file named with `--repo` is attached only when all of these hold:

- git lists it: tracked, or untracked and not ignored;
- `git check-ignore --no-index` does not match it, so a file that was force-added past `.gitignore` (a committed `.env`, say) is still refused;
- its name is not a secret file name (`.env`, `.env.*` except `.example`/`.sample`/`.template`, `.envrc`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.ppk`, `*.jks`, SSH keys, `.npmrc`, `.pypirc`, `.netrc`, `.git-credentials`, `credentials.json`, `service-account*.json`, `*.tfvars`, `*.tfstate`, `secrets.*`);
- it is not marked skip-worktree or assume-unchanged (local edits git hides), has no content filter in `.gitattributes` (git-crypt, transcrypt, LFS), and is not a submodule;
- no link or junction sits anywhere on its path, it is not a hard link (whose content can also live under an ignored name or outside the repository), and it is a regular UTF-8 text file inside the repository. Cloud placeholders from OneDrive or Dropbox are not links and pass.

A folder brings in its tracked files only; untracked files have to be named one by one. **If any file Claude named is refused, nothing is sent** and the script exits 3 with the reasons. The same happens when the files add up to more than `--max-bytes` (500 KB by default, about 125k tokens): it lists the sizes so Claude can name fewer. `--dry-run` shows what would be attached without sending anything, and `--save-request <path>` writes the exact request body for an audit.

`--diff` applies the same rules to every changed file and builds the diff with textconv off, so a force-added `.env` or a git-crypt file never shows up as a hunk. A raw `git diff` pasted into the brief would skip all of that, which is why the review skill no longer builds the diff by hand.

Git does the ignore logic, so `.gitignore` files at every level, `.git/info/exclude`, your global `core.excludesFile` and worktrees all count, with no parser of our own.

**What this does not cover.** A tracked file with a secret in it and no ignore rule or telling name still passes: git has no way to know. And the brief is outside the check: if Claude pastes something into it, it is sent.

## Commands

**`/gemini:review [--base <ref>] [--repo <paths>] [--model <m>] [--thinking low|high] [focus ...]`** Claude writes the intent, what earlier reviews already fixed, and the repo rules that apply into the brief; the script adds the diff (working tree, or `<base>...HEAD`) built from files git allows. With `--repo` it adds whole files around the diff. You get Gemini's numbered findings with severities verbatim, then Claude's own read. Nothing is edited.

**`/gemini:rescue [--repo <paths>] [--model <m>] [--thinking low|high] <ask>`** One question to Gemini, read-only. Claude writes the brief and, when the ask needs real code, names the files.

"Ask both" or "all experts" runs Codex and Gemini in parallel. A bare "second opinion" is left to the Codex plugin so the two do not compete for it.

**`--model`** takes `carbon` (default), `argon`, `flash`, `pro`, or an exact id. Aliases resolve to the newest matching model available that day (on 2026-11-11: `gemini-4-carbon`, `gemini-4-argon`, `gemini-flash-latest`, `gemini-pro-latest`). Ids are checked to be plain tokens before they go into the request URL.

**`--thinking`** is `high` by default and always sent explicitly, because the API's unset default differs by model. Measured 2026-11-11 on one small input: `gemini-4-carbon` produced no thinking tokens with the level unset (same as `low`) and 862 with `high`; `gemini-flash-latest` thought about as much unset as with `high` (554 vs 545) and not at all with `low`. Thinking shares the output budget with the answer: on a 116 KB request `gemini-4-carbon` (32,768 output tokens) once spent all of it thinking and returned nothing. The script now asks for the model's full output limit and, if the answer is still empty for that reason, retries once with thinking `low` and says so.

A request can take several minutes with thinking on (a 2,261-line diff took more than five), so the skills run the script in background Bash. The script allows 15 minutes per request.

## How this compares with the Codex plugin

The Codex plugin runs the Codex CLI with a read-only sandbox. The sandbox blocks writes while reads still go through, and the plugin does no `.gitignore` handling: Codex reads files with ordinary shell commands, and whatever it reads goes to OpenAI's API. This plugin takes the opposite approach: Gemini does not explore at all, it gets what Claude chose and git allowed.

An earlier version let the Gemini CLI explore the repository itself, like Codex. Three review rounds kept finding ways its own `.gitignore` filtering let ignored content or names through (a search tool that skips the filter, launching from a subfolder, global and worktree excludes it never reads, `.geminiignore` negation, links, path case on Windows, skills and context files inlined into the prompt). `.gitignore` lists what not to commit; it was never meant as a security boundary, and that CLI does not treat it as one. That mode is parked in issue #14.

## The canary test

A scratch repo held a unique marker string in a gitignored folder, a force-added ignored file, a file ignored only through `core.excludesFile`, a committed `.env`, a skip-worktree file with local edits, and a path that reaches the ignored folder through a junction. Each was named with `--repo` (2026-11-12, Windows 11):

| Case | Named with `--repo` | Result |
|---|---|---|
| Two tracked files | `src/app.py src/util.py` | attached; the live answer (`42`) needed both |
| Folder | `src` | its two tracked files; the untracked draft left out |
| Untracked, not ignored, named | `src/draft.py` | attached |
| Gitignored folder | `secrets/s.env` | refused, nothing sent (exit 3) |
| Force-added past `.gitignore` | `notes.canary` | refused by `git check-ignore --no-index` |
| Ignored only through `core.excludesFile` | `excluded.txt` | refused |
| Committed `.env` | `.env` | refused as a secret file name |
| Skip-worktree file with local edits | `local.cfg` | refused |
| Junction into the ignored folder | `lnk/s.env` | refused: git itself lists this path as shareable, the link check is what stops it |
| Outside the repository | `../gate-excludes.txt` | refused |
| One allowed plus one ignored | `src/app.py secrets/s.env` | refused as a whole; no request was built, live run included |

The marker appeared in no output and in no saved request body.

To rerun it, build the same repo and run each case with `--dry-run`, then one allowed and one mixed case with `--save-request` and search the saved body for the marker.

## Exit codes

`0` ok, `1` failure (key, HTTP error, bad model id or base ref), `2` usage error, `3` `--repo` or `--diff` refused, or the repository could not be read (nothing was sent), `5` unknown model alias.

## Not in v1

Agent mode (#14), `--resume`, `status`, `result`, `cancel`, `transfer`, a stop-time review hook, a subagent type, write mode, a background job store, reading Claude Code `permissions.deny` rules.
