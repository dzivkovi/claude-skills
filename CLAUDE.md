# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A personal library of portable skill `.zip` files for Claude.ai. Each skill is a ZIP archive (the skill folder at the archive root) containing instructions (`SKILL.md`), reference docs, setup scripts, and sample assets. Users upload the `.zip` under Claude.ai Settings > Skills to permanently extend Claude's behavior. (claude.ai requires a `.zip`, not the older `.skill` extension.)

## Build Commands

```bash
# Build all skills into releases/
./scripts/build-skills.sh

# Build a single skill by name
./scripts/build-skills.sh branded-docx
```

The build script zips each skill folder that contains a `SKILL.md` and outputs `releases/<skill-name>.zip` (skill folder at the archive root, as claude.ai requires).

## Skill Folder Convention

Every skill under `skills/<skill-name>/` follows this structure:

| Path | Purpose |
|------|---------|
| `SKILL.md` | Runtime instructions Claude reads (required YAML frontmatter: `name`, `description`; optional: `metadata`, `license`, `compatibility`) |
| `references/` | Human-readable docs Claude consults (brand systems, setup guides) |
| `scripts/setup/` | One-time setup automation (font installers, env checks) |
| `assets/` | Sample outputs and templates for previewing |

## Current Skills

- **branded-docx** — Generates `.docx` files styled with pluggable brand themes. Ships with five brands: **coral** (Anthropic visual identity: Poppins + Georgia, warm red accent), **remax** (RE/MAX Bridge palette: Metropolis + Arial, navy/red), **jasminahomes** (PropTech Luxury hybrid: RE/MAX colors on Coral's dense layout, Poppins + Georgia), **accessible** (high-readability theme for glasses wearers: Arial + Verdana, deep blue palette, brand-neutral - calibrated for presbyopia, not low vision), and **magma** (Magma Inc. house identity from magmainc.ca: Montserrat as the single typeface with hierarchy by weight, Bridge Blue navy signature, two-reds-chosen-by-surface rule). Add new brands by creating a single `.md` file in `brands/`. Extends the base `docx` skill.
- **branded-pptx** — Generates `.pptx` decks with the same pluggable-brand model, layered on Anthropic's base `pptx` skill. Distils prose onto slide faces and pushes full wording into speaker notes via `addNotes()`. Ships the **magma** brand today (shares Magma's palette with branded-docx so a deck and its document read as one identity; each skill keeps its own `brands/` copy). Currently version 0.1.0.

## Key Architectural Notes

- Skills are self-contained in *packaging*, not in *capability*: each folder zips into a standalone `.zip` that carries everything it defines (SKILL.md, brand files, logos), but the Skills format has no dependency manifest - there is no `requires:` field, so a skill cannot declare or auto-install another skill. `branded-docx` and `branded-pptx` are deliberately thin brand layers that expect the base `docx`/`pptx` skill to be installed separately; if a base skill is absent they still load and trigger, but Claude falls back on general knowledge instead of the base skill's codified rules.
- `SKILL.md` is the entry point Claude reads at runtime - its `description` field controls trigger-phrase matching.
- `branded-docx` layers on the base `docx` skill and `branded-pptx` on the base `pptx` skill (neither base lives in this repo) for the technical generation rules. Brand themes live in each skill's `brands/*.md` - one file per brand. Runtime libraries (`docx`, `pptxgenjs`) and the slide-QA binaries (LibreOffice, Poppler) are not bundled either; each SKILL.md's Setup section carries the install commands, which Claude runs in whatever sandbox executes the skill (an ephemeral Linux container on claude.ai, your real machine under Claude Code).
- `.zip` files in `releases/` are binary artifacts committed to git; they are built from source via `build-skills.sh` and attached to per-skill GitHub Releases for non-programmer download.

## Evaluation

- Skills with eval coverage keep artifacts in `<skill-name>-workspace/` (e.g. `branded-docx-workspace/`): `trigger-eval.json` + `eval_review.html` + a `README.md` explaining the snapshot. Raw loop output lives in `run-results/` and is gitignored — it's reproducible from the eval set.
- The SKILL.md `description` field has a **1024-character upload cap**. Measure before every commit: `python -c "import re,pathlib; md=pathlib.Path('skills/<name>/SKILL.md').read_text(encoding='utf-8'); print(len(re.search(r'description:\\s*\"([^\"]+)\"', md).group(1)))"`. Uploads silently reject longer values with *"field 'description' in SKILL.md must be at most 1024 characters."*
- On Windows, prefix `run_loop` invocations with `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` — the default `cp1252` codec crashes when the live report writes a `✗` character.
- Re-run trigger evals whenever a skill description changes materially. Read per-query `trigger_rate`, not just the pass rate — a description that never fires gets a free ~50% score on balanced evals.
- Deeper teaching context lives in the main [README.md](./README.md) "Why I evaluate my skills" section and in each skill's workspace README. Don't duplicate that here.
