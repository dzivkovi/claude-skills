# claude-skills

Personal [Claude.ai](https://claude.ai) skill library by [Daniel Zivkovic](https://www.linkedin.com/in/magmainc/).

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
| [branded-docx](./skills/branded-docx/) | Generates Word documents with pluggable brand themes. Ships with four brands (see below). Add new brands by creating one `.md` file. | `branded report`, `coral docx`, `jasminahomes style`, `accessible`, `large print`, `my branding`, `professional Word doc` |

### Available brands

| Brand | File | Identity | Typography | Use case |
|-------|------|----------|------------|----------|
| **Coral** | [coral.md](./skills/branded-docx/brands/coral.md) | Anthropic visual identity - warm red accent, off-white tone | Poppins + Georgia | Client reports, tech briefs, polished deliverables |
| **RE/MAX** | [remax.md](./skills/branded-docx/brands/remax.md) | RE/MAX Bridge palette - deep navy, bridge red, warm neutrals | Metropolis + Arial | Real estate branded documents |
| **Jasmina Homes** | [jasminahomes.md](./skills/branded-docx/brands/jasminahomes.md) | PropTech Luxury hybrid - RE/MAX colors on Coral's dense, modern layout | Poppins + Georgia | Real estate documents with tech-forward feel |
| **Accessible** | [accessible.md](./skills/branded-docx/brands/accessible.md) | High-readability theme for glasses wearers - WCAG-grounded contrast, deep blue accent that prints crisp, brand-neutral | Arial + Verdana (both built-in) | Printed documents for adult readers with reading glasses (presbyopia) - not a low-vision theme |

More skills will be added as the need arises.

---

## Repo structure

```
claude-skills/
  skills/
    branded-docx/                     # Skill: branded Word documents
      SKILL.md                          # Brand-agnostic engine
      brands/
        coral.md                        # Anthropic visual identity theme
        remax.md                        # RE/MAX Bridge palette theme
        jasminahomes.md                 # PropTech Luxury hybrid theme
        accessible.md                   # High-readability theme for glasses wearers
        coral-logo.png                  # Coral logo
        remax-logo.png                  # RE/MAX logo (400x245px)
  releases/
    branded-docx.skill                # Ready-to-upload build (ZIP)
  scripts/
    build-skills.sh                     # Packages skills/ into releases/
  README.md
```

Each skill follows the same folder convention:
- `SKILL.md` - what Claude reads at runtime (the brain)
- `brands/` - pluggable theme files (one per brand identity)

---

## Installing a skill

1. Download the `.skill` file from the [`releases/`](./releases/) folder (or the [Releases](../../releases) page once available)
2. Go to [claude.ai](https://claude.ai) > Settings > Capabilities > Skills
3. Click "Upload skill" and select the `.skill` file
4. Done - the skill is active in all future conversations

### First-time setup (branded-docx)

The branded-docx skill requires Node.js and `npm install -g docx`. Each brand file lists its font requirements:

| Brand | Fonts needed |
|-------|-------------|
| Coral | Poppins ([Google Fonts](https://fonts.google.com/specimen/Poppins)) + Georgia (built-in) |
| RE/MAX | Metropolis ([GitHub](https://github.com/chrismsimpson/Metropolis)) + Arial (built-in) |
| Jasmina Homes | Poppins ([Google Fonts](https://fonts.google.com/specimen/Poppins)) + Georgia (built-in) |
| Accessible | Arial (built-in) + Verdana (built-in) - no install required |

---

## Sharing skills

The `.skill` file is self-contained. Share it exactly as you would share a ZIP - email, Dropbox, USB. The recipient uploads it to their own Claude settings. No accounts, no dependency on this repo.

---

## Licence

MIT. Use freely, adapt as needed, attribution appreciated but not required.
