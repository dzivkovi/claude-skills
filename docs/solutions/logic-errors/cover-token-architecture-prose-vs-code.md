---
title: "Fix branded-docx cover page styling: COVER token architecture"
date: 2026-03-09
category: logic-errors
tags:
  - branded-docx
  - docx-js
  - claude-skill
  - cover-page
  - prompt-engineering
  - token-architecture
component: skills/branded-docx
severity: high
symptoms:
  - "Claude copies coverPage code template literally from SKILL.md, ignoring prose styling instructions in brand files"
  - "characterSpacing and allCaps directives in remax.md brand file have no effect on generated cover pages"
root_causes:
  - "Helper Function Trap: Claude treats code templates as authoritative and prose instructions as suggestions, so prose overrides in brand files are silently ignored"
resolution_type: architectural
version: 2.2.0
see_also:
  - "../ui-bugs/variable-font-pdf-hairline-rendering.md"
---

# COVER Token Architecture: Prose vs Code in Skill Templates

## Problem

Claude generated RE/MAX cover pages without luxury typography (no letter spacing, no ALL CAPS) despite explicit prose instructions in `remax.md` saying "Cover title should use characterSpacing: 40" and "cover category should use allCaps: true."

## Investigation

Gemini AI reviewed the output and diagnosed the **"Helper Function Trap"**: when `SKILL.md` contains a code template for `coverPage()`, Claude copies it literally and ignores prose instructions in brand files. The template acts as the authoritative source; natural-language overrides in brand `.md` files have no effect.

## Root Cause

The `coverPage` template in `SKILL.md` hardcoded `BRAND.accent` for colors and had no properties for `characterSpacing` or `allCaps`. Prose instructions in brand files were silently dropped because no corresponding slot existed in the code template.

**Key insight**: Templates are gravity wells. Once a code template exists, Claude orbits it. Any instruction not inside (or directly referenced by) the template is effectively invisible.

## Solution

Created a **COVER object architecture** with 5 dedicated tokens that each brand file defines:

```javascript
const COVER = {
  barColor: BRAND.secondary,       // bar color at top
  categoryColor: BRAND.secondary,  // category text color
  categorySpacing: 40,             // letter spacing in TWIPs (40 = 2pt expanded)
  categoryCaps: true,              // ALL CAPS category line
  titleSpacing: 40,                // title letter spacing in TWIPs
};
```

The `SKILL.md` `coverPage` template was updated to reference `COVER.*` tokens:

```javascript
// Before (hardcoded):
border: { top: { style: BorderStyle.SINGLE, size: 48, color: BRAND.accent, space: 0 } },
children: [new TextRun({ text: category, font: BRAND.heading, size: 44,
  bold: true, color: BRAND.accent })]

// After (tokenized):
border: { top: { style: BorderStyle.SINGLE, size: 48, color: COVER.barColor, space: 0 } },
children: [new TextRun({ text: category, font: BRAND.heading, size: 44,
  bold: true, color: COVER.categoryColor,
  characterSpacing: COVER.categorySpacing, allCaps: COVER.categoryCaps })]
```

`SKILL.md` provides safe defaults when a brand does not define COVER:

| Token | Default |
|-------|---------|
| `barColor` | `BRAND.accent` |
| `categoryColor` | `BRAND.accent` |
| `categorySpacing` | `0` |
| `categoryCaps` | `false` |
| `titleSpacing` | `0` |

## Verification

Coral v8 generated with COVER tokens (all defaults), XML diff against v6 showed only a timestamp change and a harmless `caps="false"` attribute — functionally identical output, confirming backward compatibility.

## Files Changed

- `skills/branded-docx/SKILL.md` — coverPage template updated to use COVER.* tokens (v2.1.0 -> v2.2.0)
- `skills/branded-docx/brands/coral.md` — added COVER object (all defaults)
- `skills/branded-docx/brands/remax.md` — added COVER object (luxury typography values)

## Prevention

### Design Principle

**"If Claude needs to do it, put it in code; prose is for humans."**

- Encode all machine-actionable styling as structured tokens, never as prose
- When adding a new brand, require a complete token object (COVER, BRAND, DEFAULTS) before the brand is considered valid
- When extending SKILL.md with new template functions, audit every brand file for styling details that live only in prose

### Detection

- **Template-vs-prose audit**: Before shipping, scan brand `.md` files for styling keywords (font-size, color, margin, weight) outside code blocks — flag as warnings
- **Render test**: After any brand or template change, generate a document with a one-line prompt. If styling is missing, it was in prose and got ignored
- **Token coverage check**: When adding a new brand, compare its token keys against existing brands. Missing keys = prose reliance

### Best Practices

1. **Templates are gravity wells** — anything outside them gets ignored
2. **One source of truth per property** — never define the same styling in both a token and prose
3. **Additive token discipline** — when introducing a new visual property, add it to the token schema first, update all brand files, then update the template. Never go template-first

## Related

- [Variable font PDF hairline rendering](../ui-bugs/variable-font-pdf-hairline-rendering.md) — the other half of the v2.2.0 RE/MAX brand fix
- [Multi-brand architecture refactor](../integration-issues/refactor-single-brand-to-pluggable-multi-brand-architecture.md) — the original BRAND token architecture
- [Skill building best practices](../../skill-building-best-practices.md) — "Instructions not followed" troubleshooting
