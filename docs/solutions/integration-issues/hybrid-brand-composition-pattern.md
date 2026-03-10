---
title: Hybrid Brand Architecture — Combining Layout + Color Palettes in branded-docx
category: integration-issues
tags:
  - branded-docx
  - brand-tokens
  - color-tokens
  - typography
  - print-safety
  - proptech
  - skill-description
  - trigger-phrases
severity: medium
components:
  - skills/branded-docx/brands/jasminahomes.md
  - skills/branded-docx/SKILL.md
  - README.md
  - CLAUDE.md
  - docs/skill-building-best-practices.md
date_solved: 2026-03-09
summary: |
  Created a hybrid brand theme (jasminahomes.md) combining Coral's layout architecture
  (Poppins/Georgia, data-dense tables, tight spacing) with RE/MAX's navy-red color palette.
  Solved five design issues: toner-trap prevention, serif font rationale, desaturated callout
  tints, table cell spacing, and COVER token configuration. Also optimized SKILL.md description
  for possessive/casual trigger phrases.
---

# Hybrid Brand Composition Pattern

## Problem

A client (real estate agent) needed documents that combined:
- The **modern, data-dense layout** of the Coral brand (Anthropic visual identity) — tight spacing, Poppins/Georgia typography, analytical feel
- The **authoritative color palette** of the RE/MAX brand — Bridge Blue `#0C2749`, Bridge Red `#AA1120`, warm cream-gray neutrals

No mechanism existed for composing two brands. Each brand file was a standalone monolith.

## Solution: Design System Composition

Created `skills/branded-docx/brands/jasminahomes.md` by taking the **structural DNA** (font stack, spacing rhythm, COVER tokens, brandStyles shape) from `coral.md` and the **chromatic DNA** (palette, tints, accent semantics) from `remax.md`.

### Key Design Decisions

#### 1. Toner Trap Prevention

**Problem:** Coral uses `light: "FAF9F5"` (off-white) as its page tone. When printed, the printer sprays a fine toner dusting across every page to achieve that off-white — tripling toner cost and making paper feel wavy.

**Fix:** Set `light: "FFFFFF"` (pure white) and added a Print Tips section advising users to buy cream/natural paper (28-32lb) instead of tinting the digital document. The physical paper provides the warmth; the digital document stays clean.

#### 2. Serif Font Override

**Problem:** RE/MAX brand guidelines strictly forbid serif fonts. But the hybrid intentionally breaks this rule.

**Rationale:** Poppins (geometric sans headings) + Georgia (editorial serif body) creates a "PropTech Luxury" pairing — the same contrast used by Stripe, McKinsey, and wealth management firms. The geometric precision of Poppins signals "modern analytical rigor" while Georgia's warmer letterforms signal "trustworthy authority." This is the hybrid's signature — it wouldn't work with Arial body text.

#### 3. Desaturated Callout Tints

**Problem:** Standard highlight colors (bright green, neon yellow, vivid red) clash with the navy/red palette and look cheap.

**Fix:** Created three luxury-adjusted tints, each desaturated and gray-shifted to read as "expensive stationery" rather than "colored highlighter":

| Tint | Hex | Base Color | Use |
|------|-----|------------|-----|
| Sage green | `E8F0EA` | Green | Success/positive callouts |
| Blush rose | `FDF5F5` | Red | Award/caution callouts |
| Ice blue | `F0F2F8` | Blue | Info/emphasis callouts |

#### 4. Table Cell Spacing

**Problem:** Coral's default table cell margins (~40 DXA) were too tight for real estate documents with longer text content.

**Fix:** Increased top/bottom cell margins to ~48 DXA (20% more breathable). Keeps the professional density without feeling cramped.

#### 5. COVER Token Configuration

**Decision:** Used RE/MAX's red bar heritage (`barColor: BRAND.secondary`) but Coral's clean defaults:
- `categorySpacing: 0` (no luxury letter tracking — modern tech feel)
- `categoryCaps: false` (normal case — contemporary)
- `titleSpacing: 0` (dense, analytical)

This gives the cover page RE/MAX's red accent bar without the letter-spaced luxury typography that would clash with Coral's dense headings.

### SKILL.md Description Optimization

**Problem:** The skill description didn't include trigger phrases for the new brand. Queries like "use the Jasmina brand" or "format this in my branding" wouldn't trigger the skill.

**Fix:** Added to the description:
- Explicit brand names: `jasminahomes`, `Jasmina brand`, `Jasmina Homes`
- Possessive/casual patterns: `my branding`, `my brand`, `in my style`, `my usual theme`
- Real estate document types: `CMAs`, `listing presentations`, `market reports`

**Key insight:** Trigger phrases should **name the brand**, not describe its colors. "Navy and red" is noise — it bypasses the brand system and invites Claude to improvise. "Jasmina brand" is signal — it tells Claude which brand file to load.

### Documentation Updated

- `README.md` — Added brand table, repo structure, font requirements for all 3 brands
- `CLAUDE.md` — Updated Current Skills to list all 3 brands
- `releases/README.md` — Updated description
- `docs/skill-building-best-practices.md` — Added guidance on possessive/casual trigger phrasing and brand name variations

## Prevention / Best Practices

1. **When composing brands:** Decide which brand provides structure (fonts, spacing, COVER defaults) and which provides color (palette, tints). Never mix fonts from both — pick one font stack.
2. **Always use `FFFFFF` for `light` token** if the brand will be printed. Add a Print Tips section instead of tinting the page background.
3. **When adding new brands:** Update the SKILL.md description with the brand name and common variations. Users say brand names in many ways — list them all.
4. **Callout tints must complement the palette.** Take the base color, wash it out with white until it barely registers, then shift slightly toward gray. The formula: high lightness (95-98%), low saturation (5-15%).

## Reusable Pattern

This "design system composition" approach is reusable for any future hybrid brand:

```
1. Pick STRUCTURE source → copy fonts, spacing rhythm, COVER defaults, brandStyles shape
2. Pick COLOR source → swap accent, secondary, tertiary, dark, midGray, lightGray
3. Derive tints → desaturate each accent color to 95-98% lightness
4. Set light to FFFFFF → add Print Tips if printable
5. Adjust table margins → test with real content
6. Update SKILL.md description → add brand name + variations
```

## Cross-References

- [Pluggable multi-brand architecture](refactor-single-brand-to-pluggable-multi-brand-architecture.md) — foundational architecture this pattern extends
- [COVER token architecture](../logic-errors/cover-token-architecture-prose-vs-code.md) — COVER token design (5 tokens: barColor, categoryColor, categorySpacing, categoryCaps, titleSpacing)
- [Variable font PDF fix](../ui-bugs/variable-font-pdf-hairline-rendering.md) — why jasminahomes uses Poppins (static TTFs) instead of Montserrat (variable font)
- [Table cell text clipping](../ui-bugs/docx-table-cell-text-clipping.md) — canonical brandTable() pattern and spacing fixes
