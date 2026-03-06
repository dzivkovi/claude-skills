# Pre-Built Skills

Download a ready-to-use `.skill` file and upload it to Claude.

## Quick Download

| Skill            | Download                                    | Description                       |
|------------------|---------------------------------------------|-----------------------------------|
| **branded-docx** | [branded-docx.skill](./branded-docx.skill)  | Anthropic-branded Word documents  |

## Installation

1. Download the `.skill` file above
2. Open Claude.ai > Settings > Capabilities > Skills
3. Click "Upload skill" and select the file
4. Done - Claude uses it automatically for matching requests

## Building from Source

```bash
git clone https://github.com/dzivkovi/claude-skills
cd claude-skills

# Build all skills
./scripts/build-skills.sh

# Or one specific skill
./scripts/build-skills.sh branded-docx
```

Built files appear in `releases/`.
