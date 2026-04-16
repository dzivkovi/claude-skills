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

## Why I evaluate my skills (and you should too)

Your skill's `description` field tells Claude when to use it. Evals are how you check whether that instruction is actually working — whether Claude picks up your skill when a real user asks for what it does. Without evals, a skill that works perfectly on your desk can silently fail in the wild because the description doesn't match how people really phrase things.

### The two kinds

- **Trigger evals** — does Claude fire the skill when a user asks? Tests *description quality*.
- **Behaviour evals** — when it fires, does the output come out right? Tests *instruction quality*.

### Start here in 5 minutes

1. Open [`branded-docx-workspace/trigger-eval.json`](./branded-docx-workspace/trigger-eval.json) — 20 real-world queries, 10 that should trigger this skill, 10 that shouldn't. Skim them: that's what a basic trigger-eval set looks like.
2. Open [`eval_review.html`](./branded-docx-workspace/eval_review.html) in a browser — click through, toggle `should_trigger`, add your own queries, export an updated set.
3. When you're ready to do this for *your own* skill, install Anthropic's [`/skill-creator`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md) plugin, open a Claude Code session in your skill's folder, and say something like *"use skill-creator to run trigger evals against my skill."* It generates the queries, runs them against Claude, and reports trigger accuracy.

You don't need to understand the jargon yet — reading the JSON file teaches you what good queries look like, and running the loop once teaches you the rest.

### What running it on this skill taught me

I ran the full loop against v2.5.0 and got 6/12 on training queries and 4/8 on held-back test queries — stable across all 5 iterations. (The split is skill-creator's way of checking whether a description overfits to the exact queries it's tuned on: 60% used to guide improvements, 40% held back to score honestly.) That score *looked* like "the description is already optimal." It wasn't. Every one of the 10 positive queries had `trigger_rate = 0.0` — the skill never fired, across 3 attempts each — and every negative query passed trivially by also not firing. **The whole score was a clean pass-by-default.** Three lessons stuck:

- **Never trust the headline score alone — read per-query `trigger_rate`.** A description that never fires gets a free 50% on a balanced eval.
- **The `description` field has a hard 1024-character upload cap.** Mine was 1192 chars after v2.5.0; uploads silently rejected it with *"field 'description' in SKILL.md must be at most 1024 characters."* I trimmed it to 964 (same coverage, less synonym redundancy) and rebuilt.
- **On Windows, prefix `run_loop` with `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`** — the default `cp1252` codec crashes when the live HTML report writes a `✗` character.

### The state of this eval suite

| Check | Status |
|---|---|
| Description fits 1024-char upload cap | ✅ 964 / 1024 |
| Trigger-eval loop runs end-to-end | ✅ 20 queries × 5 iterations |
| Negative queries correctly don't trigger | ✅ 10 / 10 |
| Skill fires on natural-language queries | ⚠️ 0 / 10 under the automated test — but that test only checks one of several ways a skill can fire; an independent sanity check is still pending (see workspace README) |
| Behaviour evals (does the .docx come out right?) | ⬜ Not started |

Honest verdict: the suite has **real coverage on triggering but no coverage on output quality**. The 0 / 10 result is ambiguous — the tool tests one specific invocation path, not all of them. Open questions and next-cycle tasks live in [`branded-docx-workspace/README.md`](./branded-docx-workspace/).

### Deep dive

- [`/skill-creator` docs](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md) — the framework that runs the loop
- [Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md) — Anthropic's guidance on writing descriptions that route well

---

## Licence

MIT. Use freely, adapt as needed, attribution appreciated but not required.
