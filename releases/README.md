# Pre-Built Skills

Download a ready-to-use `.zip` and upload it to Claude. No coding required.

## Quick Download

| Skill | Download | Description |
|-------|----------|-------------|
| **branded-docx** | [branded-docx.zip](./branded-docx.zip) | Branded Word documents (Magma, Coral, RE/MAX, Jasmina Homes, Accessible themes) |
| **branded-pptx** | [branded-pptx.zip](./branded-pptx.zip) | Branded PowerPoint decks (Magma theme) |

## Installation

1. Download the `.zip` above
2. In Claude.ai, open **Settings** and find **Skills** (under Capabilities, or Customize, depending on your plan)
3. Click **Create skill** (the **+**) and select the `.zip`
4. Done - Claude uses it automatically for matching requests

claude.ai requires a `.zip` with the skill folder at the archive root (not the older `.skill` extension). The files here are built that way.

## Building from Source

```bash
git clone https://github.com/dzivkovi/claude-skills
cd claude-skills

# Build all skills
./scripts/build-skills.sh

# Or one specific skill
./scripts/build-skills.sh branded-pptx
```

Built `.zip` files appear in `releases/`.
