# claude-skills

Personal [Claude.ai](https://claude.ai) skill library by [@dzivkovi](https://github.com/dzivkovi).

Each skill is a portable `.skill` file (a ZIP under the hood) that you upload once to Claude's settings and it permanently changes how Claude behaves - no prompting, no reminding, no repeating yourself.

---

## Why I built this

There is a trust mechanic at work in how high-performing consultants and creators present their work. Call it **borrowed authority**: when your output consistently looks like it came from a credible institution, people unconsciously extend that institution's reputation to you.

I first noticed the pattern watching creators like [Ruben Hassid](https://www.linkedin.com/in/ruben-hassid/) and others in the AI consulting space. Their posts, decks, and documents don't just contain good ideas - they *look* the part. The visual language signals that the author moves in serious circles. It is not deception; it is the same logic behind choosing a well-designed business card over a plain one. The content earns attention, the presentation earns trust.

Anthropic happens to have one of the cleanest brand systems in the AI space: a restrained palette, a warm serif body font, a single coral accent used with discipline. When I produce reports, briefs, and playbooks for clients, I want that visual quality without thinking about it each time. So the first skill I built automates exactly that: every `.docx` Claude generates now looks like it came out of Anthropic's design team.

The result is documents that feel native to the AI world, carry subtle credibility by association, and most importantly - just look good without extra effort.

---

## How Claude skills work

A skill is a folder of instructions, code templates, reference documents, and setup scripts, compressed into a single `.skill` file. When uploaded to Claude:

1. Claude reads the `SKILL.md` file to understand the new capability
2. Trigger phrases in your chat automatically activate the relevant skill
3. Reference files, code templates, and brand tokens are available to Claude throughout the conversation

Skills are installed once under **Settings > Capabilities > Skills** and persist across all future conversations.

---

## Skills in this repo

| Skill | What it does | Trigger phrases |
|-------|-------------|-----------------|
| [branded-docx](./skills/branded-docx/) | Generates Word documents styled with Anthropic's visual identity (Poppins headings, Georgia body, coral `#D97757` accents) | `branded report`, `professional Word doc`, `Anthropic style`, `make it look professional` |

More skills will be added as the need arises.

---

## Repo structure

```
claude-skills/
  skills/
    branded-docx/                       # Skill 01: Anthropic-styled Word documents
      SKILL.md                          # Instructions Claude reads at runtime
      references/
        brand-system.md                 # Full color, typography, and layout reference
        setup-and-prerequisites.md      # Node.js, fonts, npm setup guide
      scripts/
        setup/
          install-fonts-windows.ps1     # One-click Poppins installer for Windows
      assets/
        branded-sample.docx             # Preview the output before generating
  README.md
```

Each skill follows the same folder convention:
- `SKILL.md` - what Claude reads at runtime (the brain)
- `references/` - human-readable docs Claude consults when relevant
- `scripts/setup/` - one-time setup automation (font installers, environment checks)
- `assets/` - sample outputs and templates so you can preview before generating

---

## Installing a skill

1. Download the `.skill` file from the [`skills/`](./skills/) folder (or the [Releases](../../releases) page once available)
2. Go to [claude.ai](https://claude.ai) > Settings > Capabilities > Skills
3. Click "Upload skill" and select the `.skill` file
4. Done - the skill is active in all future conversations

### First-time setup (branded-docx)

The branded-docx skill requires two fonts and Node.js. See [`setup-and-prerequisites.md`](./skills/branded-docx/references/setup-and-prerequisites.md) for full instructions, or run the Windows font installer directly:

```
skills/branded-docx/scripts/setup/install-fonts-windows.ps1
```

Right-click > Run with PowerShell. Takes about 30 seconds.

---

## Sharing skills

The `.skill` file is self-contained. Share it exactly as you would share a ZIP - email, Dropbox, USB. The recipient uploads it to their own Claude settings. No accounts, no dependency on this repo.

---

## Licence

MIT. Use freely, adapt as needed, attribution appreciated but not required.
