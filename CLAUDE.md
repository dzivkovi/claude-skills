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
