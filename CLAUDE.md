# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A personal library of portable `.skill` files for Claude.ai. Each skill is a ZIP archive containing instructions (`SKILL.md`), reference docs, setup scripts, and sample assets. Users upload `.skill` files to Claude.ai Settings > Capabilities > Skills to permanently extend Claude's behavior.

## Build Commands

```bash
# Build all skills into releases/
./scripts/build-skills.sh

# Build a single skill by name
./scripts/build-skills.sh branded-docx
```

The build script zips each skill folder that contains a `SKILL.md` and outputs `releases/<skill-name>.skill`.

## Skill Folder Convention

Every skill under `skills/<skill-name>/` follows this structure:

| Path | Purpose |
|------|---------|
| `SKILL.md` | Runtime instructions Claude reads (required YAML frontmatter: `name`, `description`; optional: `metadata`, `license`, `compatibility`) |
| `references/` | Human-readable docs Claude consults (brand systems, setup guides) |
| `scripts/setup/` | One-time setup automation (font installers, env checks) |
| `assets/` | Sample outputs and templates for previewing |

## Current Skills

- **branded-docx** — Generates `.docx` files styled with pluggable brand themes. Ships with four brands: **coral** (Anthropic visual identity: Poppins + Georgia, warm red accent), **remax** (RE/MAX Bridge palette: Metropolis + Arial, navy/red), **jasminahomes** (PropTech Luxury hybrid: RE/MAX colors on Coral's dense layout, Poppins + Georgia), and **accessible** (high-readability theme for glasses wearers: Arial + Verdana, deep blue palette, brand-neutral — calibrated for presbyopia, not low vision). Add new brands by creating a single `.md` file in `brands/`. Extends the base `docx` skill.

## Key Architectural Notes

- Skills are self-contained: each skill folder zips into a standalone `.skill` file with no cross-skill dependencies.
- `SKILL.md` is the entry point Claude reads at runtime — its `description` field controls trigger-phrase matching.
- The branded-docx skill layers on top of a separate base `docx` skill (not in this repo) for technical DOCX generation rules. Brand themes live in `brands/*.md` — one file per brand.
- `.skill` files in `releases/` are binary artifacts committed to git; they are built from source via `build-skills.sh`.

## Evaluation

- Skills with eval coverage keep artifacts in `<skill-name>-workspace/` (e.g. `branded-docx-workspace/`): `trigger-eval.json` + `eval_review.html` + a `README.md` explaining the snapshot. Raw loop output lives in `run-results/` and is gitignored — it's reproducible from the eval set.
- The SKILL.md `description` field has a **1024-character upload cap**. Measure before every commit: `python -c "import re,pathlib; md=pathlib.Path('skills/<name>/SKILL.md').read_text(encoding='utf-8'); print(len(re.search(r'description:\\s*\"([^\"]+)\"', md).group(1)))"`. Uploads silently reject longer values with *"field 'description' in SKILL.md must be at most 1024 characters."*
- On Windows, prefix `run_loop` invocations with `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` — the default `cp1252` codec crashes when the live report writes a `✗` character.
- Re-run trigger evals whenever a skill description changes materially. Read per-query `trigger_rate`, not just the pass rate — a description that never fires gets a free ~50% score on balanced evals.
- Deeper teaching context lives in the main [README.md](./README.md) "Why I evaluate my skills" section and in each skill's workspace README. Don't duplicate that here.
