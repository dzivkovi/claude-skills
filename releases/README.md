# Pre-Built Skill Releases

Download the latest pre-built skill without any setup.

## Quick Download

| Skill | Latest | Version | Notes |
|-------|--------|---------|-------|
| **branded-docx** | [branded-docx-latest.skill](./branded-docx-latest.skill) | [v1.0.0](./branded-docx-v1.0.0.skill) | Anthropic-branded Word documents |

## Installation

1. Download the `.skill` file above
2. Open Claude.ai and go to Settings
3. Navigate to the Skills section
4. Upload the downloaded `.skill` file
5. Claude will automatically use it for matching requests

To trigger `branded-docx`, say something like:
- "Convert the attached markdown to a branded Word doc."
- "Create a branded report about..."
- "Make me a professional Word doc styled like Anthropic"

## Building from Source

If you want to modify a skill and rebuild it:

```bash
git clone https://github.com/dzivkovi/claude-skills
cd claude-skills

# Build all skills
./scripts/build-skills.sh

# Build one specific skill
./scripts/build-skills.sh branded-docx
```

Built files appear in `releases/`. The script reads the `version:` field from each skill's `SKILL.md` frontmatter and produces:
- `releases/<skill-name>-v<version>.skill` - the versioned build
- `releases/<skill-name>-latest.skill` - always points to the latest version

Bump the `version:` field in `SKILL.md` before rebuilding to keep old versions around.
