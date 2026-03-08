---
title: "coral-docx skill rename and NODE_PATH fix for Claude Code"
category: integration-issues
component: coral-docx skill
symptoms:
  - "Skill name 'anthropic-styled-docx' rejected on upload"
  - "Cannot find module 'docx' in Claude Code (Git Bash)"
  - "Document quality lower in Claude Code vs Claude Desktop"
root_cause:
  - "Reserved words 'anthropic' and 'claude' forbidden in skill name field"
  - "Node.js global packages not on module search path in Git Bash"
tags: [skills, node-path, npm, git-bash, windows, docx, naming]
date_solved: 2026-03-07
---

# coral-docx skill rename and NODE_PATH fix for Claude Code

## Problem 1: Reserved word in skill name

### Symptom

The skill was originally named `branded-docx`, which was too generic. The first rename candidate `anthropic-styled-docx` would have been rejected by Claude's skill validation system.

### Discovery

Both the [Anthropic agent skills docs](../../../docs/agent-skills-overview.md) (line 228) and the [skill-building best practices guide](../../../docs/skill-building-best-practices.md) (line 75) state:

> `name`: Cannot contain reserved words: "anthropic", "claude"

This is a hard validation constraint enforced when uploading `.skill` files to Claude.ai.

### Solution

Chose `coral-docx` as the new name. "Coral" references Anthropic's signature accent color `#D97757`, which is immediately recognizable to anyone familiar with the brand. The `description` field in SKILL.md (which has no reserved word restriction) handles the full explanation.

### Files changed

Nine files updated with `replace_all` to swap `branded-docx` to `coral-docx`:

- `skills/branded-docx/` folder renamed to `skills/coral-docx/`
- `skills/coral-docx/SKILL.md` — name, description triggers, title
- `skills/coral-docx/assets/README.md` — 3 references
- `CLAUDE.md` — 3 references
- `README.md` — 7 references
- `releases/README.md` — 2 references
- `scripts/build-skills.sh` — 1 reference (usage comment)
- `docs/skill-building-best-practices.md` — 4 references
- `releases/branded-docx.skill` deleted, rebuilt as `releases/coral-docx.skill`

Verification: `grep -r "branded-docx"` returns zero matches.

---

## Problem 2: NODE_PATH missing in Git Bash

### Symptom

Documents generated via Claude Code (Git Bash on Windows 11) were lower quality than those generated via Claude Desktop. The skill uses the `docx` npm package (v9.5.3) installed globally.

### Investigation

```bash
# This fails in Git Bash when CWD is not the npm prefix:
node -e "require('docx')"
# Error: Cannot find module 'docx'

# But works with NODE_PATH set:
export NODE_PATH=$(npm root -g)
node -e "require('docx')"
# Success
```

### Root cause

Node.js installed via nvm4w places global packages at `C:\nvm4w\nodejs\node_modules`. When a script runs from a different working directory (e.g., the user's project folder), Node.js does not search the global prefix by default. `NODE_PATH` must be set explicitly.

Claude Desktop's VM likely has this configured automatically, or installs packages locally per-script. Claude Code runs scripts in the user's local environment where this configuration is missing.

### Solution

Added a NODE_PATH auto-detection preamble to every generated script in SKILL.md. The preamble uses `child_process.execSync('npm root -g')` — a hardcoded command with no user input — to locate the global modules directory and reinitialize Node's module paths at runtime.

This preamble appears in both the "Mandatory Style Overrides" section and the "Minimal Full Document Example" section of SKILL.md, so Claude always includes it in generated scripts.

Also added a troubleshooting entry to `skills/coral-docx/references/setup-and-prerequisites.md` documenting the issue and the `~/.bashrc` fix.

---

## Prevention

1. **Always check the reserved word list** before naming skills. The words "anthropic" and "claude" are forbidden in the `name` field. Use the `description` field for brand references instead.

2. **Include NODE_PATH preamble** in any skill that generates Node.js scripts using globally-installed packages. The preamble is safe (hardcoded command, no user input) and adds negligible overhead.

3. **Test `require()` resolution** from a non-npm directory before shipping a skill that depends on global packages. Run from the user's likely working directory, not from the npm prefix.

4. **Document environment differences** between Claude Desktop and Claude Code in setup guides. Claude Desktop runs in a managed VM; Claude Code runs in the user's local shell with all its configuration quirks.
