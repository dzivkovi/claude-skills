# Pre-Built Skill Releases

Download the latest pre-built skill without any setup.

## Quick Download

| Skill | Latest | Version | Notes |
|-------|--------|---------|-------|
| **branded-docx** | [branded-docx-latest.skill](./branded-docx-latest.skill) | [v1.0.0](./branded-docx-v1.0.0.skill) | Anthropic-branded Word documents |

Binaries are committed here via `git` after each release build (see below).
If a `.skill` link above returns 404, the binary hasn't been pushed yet - use the build-from-source path instead.

## Installation

1. Download the `.skill` file above
2. Open Claude.ai > Settings > Skills
3. Upload the downloaded `.skill` file
4. Claude will automatically use it for matching requests

Trigger phrases for `branded-docx`:
- "Convert the attached markdown to a branded Word doc."
- "Create a branded report about..."
- "Make me a professional Word doc styled like Anthropic"

## Building from Source

Clone the repo, edit a skill, rebuild:

```bash
git clone https://github.com/dzivkovi/claude-skills
cd claude-skills

# Build all skills
./scripts/build-skills.sh

# Or one specific skill
./scripts/build-skills.sh branded-docx
```

Built files appear in `releases/`. Commit and push to publish:

```bash
git add releases/
git commit -m "release: branded-docx v1.0.1"
git push
```

The build script reads the `version:` field from each skill's `SKILL.md` frontmatter and produces:
- `releases/<skill-name>-v<version>.skill` - versioned archive
- `releases/<skill-name>-latest.skill` - always the most recent build

Bump `version:` in `SKILL.md` before rebuilding to preserve old versions alongside the new one.
