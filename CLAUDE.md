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

## Releasing a skill (independent versioning - do all four steps)

This is an **independent-versioning monorepo**: each skill is its own independently-versioned, independently-released package, with its own SemVer and its own release line. Releasing ONE skill never touches the others' versions or releases. When you finish or update a skill, do all four steps - **skipping step 4 is the easy mistake** (the zip lands in `releases/` but nothing appears on the GitHub Releases page the README sends people to):

1. **Bump its SemVer** in `skills/<skill>/SKILL.md` `metadata.version` (MAJOR = breaking, MINOR = new capability, PATCH = fix).
2. **Build the zip:** `./scripts/build-skills.sh <skill>` -> `releases/<skill>.zip`.
3. **Commit** the source change + the rebuilt `releases/<skill>.zip` (+ any README/table rows).
4. **Cut the GitHub Release** (the canonical, browsable, immutable artifact people actually download):

   ```bash
   gh release create <skill>-v<version> releases/<skill>.zip \
     --title "<skill> v<version>" \
     --notes "what changed"
   ```

**Tag convention: `<skill>-v<version>`** (e.g. `slop-check-v0.1.0`, `branded-pptx-v0.2.0`). The per-skill prefix is what lets one repo carry many independent release lines - it is the mechanism, not decoration. The `releases/` folder is a convenience mirror of the latest zips; the tagged GitHub Release is the versioned distribution.

Worked example (slop-check, 2026-06-28): `0.1.0` in SKILL.md -> `build-skills.sh slop-check` -> commit `releases/slop-check.zip` -> `gh release create slop-check-v0.1.0 releases/slop-check.zip`. The first publish did steps 1-3 but missed step 4, so the Releases page stayed empty until the tag was cut. That gap is why this checklist exists.

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
- **branded-pptx** — Generates `.pptx` decks with the same pluggable-brand model, layered on Anthropic's base `pptx` skill. Distils prose onto slide faces and pushes full wording into speaker notes via `addNotes()`. Ships the **magma** brand today (shares Magma's palette with branded-docx so a deck and its document read as one identity; each skill keeps its own `brands/` copy). Currently version 0.2.0, which front-loads a **Preflight** (install the brand font as static Regular/Bold cuts: a bare variable font renders as "Thin" and makes the QA preview lie) and reframes slide QA as a **Definition of Done** (render every slide, fix the one or two overflow defects, declare done only after a clean render). v0.2.0 was the fix for "the same skill produced a rough deck on one machine and a sharp one on another" - the difference was environment, not the templates.
- **slop-check** — Fresh-eyes logic-and-slop review of prose: catches writing that reads like fine English but is logically, mathematically, or definitionally wrong, plus internal contradictions, drift off the piece's own stated point, and AI tells. NOT a fact-checker - a logic gate to run after the facts are verified, before publishing. One reviewer per file (fans out for many), report-only (never edits). Brand-neutral: reads each project's own `CLAUDE.md`/`AGENTS.md` for house style, so it travels unchanged. Standalone (no base skill). Currently version 0.1.0.
- **read-along** — Guided storybook walkthrough of accumulated work (a session, a PR batch, an overnight run): gathers merged PRs/issues/`work/` notes in scope, writes a self-contained ranked HTML storybook, drives the live product in a real CDP browser next to it, and runs a strict stop-and-go ("say go") protocol with a final decisions list. This is the repo's only **Claude Code workflow skill**, not a claude.ai upload: it needs a git repo, `gh`, subagents, and a browser MCP, none of which exist in the claude.ai sandbox, so it installs by dropping the folder under `~/.claude/skills/` (or a project `.claude/skills/`). Two folder-convention exceptions, both deliberate: (1) its reference doc `audio-player.md` sits BESIDE `SKILL.md` at the folder root, not under `references/`, because `SKILL.md` reads it "beside this file"; (2) its `SKILL.md` carries no `metadata.version` frontmatter (version 5 is stated in the body) and was published byte-for-byte from the author's working copy, so the release-process step 1 (bump `metadata.version`) does not apply as written - tag the GitHub Release from the body version instead. The intermediate v1-v4 development files are intentionally not shipped.

## Key Architectural Notes

- Skills are self-contained in *packaging*, not in *capability*: each folder zips into a standalone `.zip` that carries everything it defines (SKILL.md, brand files, logos), but the Skills format has no dependency manifest - there is no `requires:` field, so a skill cannot declare or auto-install another skill. `branded-docx` and `branded-pptx` are deliberately thin brand layers that expect the base `docx`/`pptx` skill to be installed separately; if a base skill is absent they still load and trigger, but Claude falls back on general knowledge instead of the base skill's codified rules.
- `SKILL.md` is the entry point Claude reads at runtime - its `description` field controls trigger-phrase matching.
- `branded-docx` layers on the base `docx` skill and `branded-pptx` on the base `pptx` skill (neither base lives in this repo) for the technical generation rules. Brand themes live in each skill's `brands/*.md` - one file per brand. Runtime libraries (`docx`, `pptxgenjs`) and the slide-QA binaries (LibreOffice, Poppler) are not bundled either; each SKILL.md's Setup section carries the install commands, which Claude runs in whatever sandbox executes the skill (an ephemeral Linux container on claude.ai, your real machine under Claude Code).
- `.zip` files in `releases/` are binary artifacts committed to git; they are built from source via `build-skills.sh` and attached to per-skill GitHub Releases for non-programmer download.
- **Font fidelity is governed by one doctrine, `references/font-fidelity.md`, copied identically into both skills** (the same self-contained-packaging reason the magma brand and logos are duplicated per skill). It covers the three font problems (absent font, wrong cut, recipient's machine), the fail-loud preflight (`scripts/setup/font_preflight.py`), the metric-compatible substitution policy (Gelasio for Georgia, never a look-alike like Lora: verified 0.00% advance-width difference vs Georgia), and embedding for distribution. The two copies and the two `font_preflight.py` copies must stay in sync; brand files and SKILL.md point at the doctrine instead of restating it. When you change one copy, change the other in the same diff.

## Evaluation

- Skills with eval coverage keep artifacts in `<skill-name>-workspace/` (e.g. `branded-docx-workspace/`): `trigger-eval.json` + `eval_review.html` + a `README.md` explaining the snapshot. Raw loop output lives in `run-results/` and is gitignored — it's reproducible from the eval set.
- The SKILL.md `description` field has a **1024-character upload cap**. Measure before every commit: `python -c "import re,pathlib; md=pathlib.Path('skills/<name>/SKILL.md').read_text(encoding='utf-8'); print(len(re.search(r'description:\\s*\"([^\"]+)\"', md).group(1)))"`. Uploads silently reject longer values with *"field 'description' in SKILL.md must be at most 1024 characters."*
- On Windows, prefix `run_loop` invocations with `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` — the default `cp1252` codec crashes when the live report writes a `✗` character.
- Re-run trigger evals whenever a skill description changes materially. Read per-query `trigger_rate`, not just the pass rate — a description that never fires gets a free ~50% score on balanced evals.
- Deeper teaching context lives in the main [README.md](./README.md) "Why I evaluate my skills" section and in each skill's workspace README. Don't duplicate that here.
